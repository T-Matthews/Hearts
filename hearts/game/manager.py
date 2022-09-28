import logging
import random
import time
from typing import Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.transaction import atomic

from hearts.bots.utils import get_bot_from_strategy
from hearts.models import Card, Deal, Game, Player, Trick

logger = logging.getLogger('django')


class GameManager:
    """
    Class to manage the business logic of the game.

    This is very much a work-in-progress and should be refactored into smaller,
    more meaningful pieces.
    """

    @atomic
    def __init__(self, game: Game):
        """Initialize the game manager with a Game object."""
        # Make the Game object accessible to instances of this class. Acquire
        # lock on game object to prevent concurrent game updates.
        self.game = Game.objects.select_for_update(nowait=True).get(id=game.id)

    @staticmethod
    def new_game(player: Player) -> Game:
        """
        Create a new Game.

        Right not this is very basic and just adds a few bots to the game. For
        this to work, you need to have at least 3 Player objects with `bot` set
        to `true`.

        This method does not start the game, it jsut creates the object.

        Args:
            player (Player): The player who is starting the game. This will
                always become player 1.

        Returns:
            Newly created Game object.
        """
        bots = Player.objects.filter(bot=True)
        # Create Game.
        game = Game.objects.create(
            player_1=player,
            player_2=bots[0],
            player_3=bots[1],
            player_4=bots[2],
        )
        logger.info('Created new game')

        return game

    def join(self, player: Player) -> None:
        """
        Join a game in progress.

        If a user tries to join a game, either from the game browser or
        otherwise, the user will take over a bot's seat if possible. If there
        is a bot to take over, then we transfer all of the current and past
        cards to the new user.
        """
        if player not in self.game.players:
            for i in range(1, 5):
                if (bot_player := getattr(self.game, f'player_{i}')).bot:
                    # Update Game.
                    setattr(self.game, f'player_{i}', player)
                    self.game.save()

                    # Update Tricks.
                    Trick.objects.filter(
                        deal__game=self.game,
                        winning_player=bot_player,
                    ).update(
                        winning_player=player,
                    )

                    # Update Cards.
                    Card.objects.filter(
                        deal__game=self.game,
                        player=bot_player,
                    ).update(
                        player=player,
                    )
                    logger.info('Joined game. Took over from bot')
                    return
            logger.info('No empty spots in game')
        else:
            logger.info('Player already in game')

    def leave(self, player: Player) -> None:
        """
        The inverse of joining a game.

        Have a bot take over for a player leaving the game.
        """
        if player in self.game.players:
            bot = Player.objects.filter(
                bot=True,
            ).exclude(
                id__in=[p.id for p in self.game.players],
            ).last()
            if bot is None:
                logger.info('Could not find bot to take over')
                return

            player_index = self.game.get_player_index(player.id)
            setattr(self.game, f'player_{player_index}', bot)
            self.game.save()

            # Update Tricks.
            Trick.objects.filter(
                deal__game=self.game,
                winning_player=player,
            ).update(
                winning_player=bot,
            )

            # Update Cards.
            Card.objects.filter(
                deal__game=self.game,
                player=player,
            ).update(
                player=bot,
            )
            logger.info('Left game. Bot taking over')

    def play(self) -> None:
        """
        Play through a trick, stopping for player input.

        This is the main method that runs the entire game. It loops through all
        players in order until everyone has taken their turn. For bots, it will
        force them to play automatically. For players, the method will return
        and then restart once the correct player has played a card.

        Once a trick is complete, the trick will get assigned a winner and a
        new trick will be delt.

        Once a deal is complete, a new deal is supposed to start. This is
        really buggy though and something freezes up at that point. Need to
        investigate.
        """
        if self.game.winning_player is not None:
            logger.info('Skipping playing game: Game already over')
            return

        logger.info('Starting game play')
        # If the pass has not happened yet, try to trigger it. Else return
        # and wait for human players to pass cards
        if not self.current_deal.has_passed:
            self.pass_cards()
            if not self.current_deal.has_passed:
                logger.info('Exiting play, waiting for pass')
                return
        self.send_game_state_to_client()

        trick = self.current_trick

        # Continuously loop until the trick has 4 cards associated with it.
        while Card.objects.filter(trick=trick).count() < 4:
            current_turn_player = self.get_current_turn()
            # If the method to get the current turn returns None then just
            # return. It's not clear exactly why this happens, but I believe
            # it's caused by players trying to go out of turn. Breaking out of
            # the method seems to work fine as the next player will start this
            # loop again once they play.
            if current_turn_player is None:
                return

            # Break out of the loop and method if a human player is up. The
            # game is essentially now paused until the human player takes their
            # turn. We should eventually add some kind of timer to this and
            # kick a human player off if inactive for too long.
            if not current_turn_player.bot:
                logger.info('Awaiting human player card')
                self.send_player_notification(
                    player=current_turn_player,
                    notification='Your up',
                )
                return

            # Make the bot play their turn.
            card = self.get_bot_card_to_play(current_turn_player)
            logger.info('Playing bot card')
            self.play_card(card)
            self.send_game_state_to_client()

        # At this point the trick has just had the fourth card played.
        # We determine the winner of the trick by finding the highest value
        # card that followed suit.
        cards_in_suit_played = list(Card.objects.filter(
            trick=trick,
            suit=trick.first_card.suit,
        ))
        cards_in_suit_played.sort(
            key=lambda x: x.value if x.value > 1 else 99,
            reverse=True
        )
        winner = cards_in_suit_played[0].player
        trick.winning_player = winner
        trick.save()
        logger.info(f'Player {self.game.get_player_index(winner.id)} takes the trick')
        for player in self.game.players:
            if player == winner:
                points = sum(c.score for c in Card.objects.filter(
                    trick=trick,
                ))
                notification_text = 'You take the trick'
                if points > 0:
                    notification_text += f'. +{points} points'
                self.send_player_notification(
                    player=player,
                    notification=notification_text,
                )
            else:
                self.send_player_notification(
                    player=player,
                    notification=f'{winner.name} takes the trick',
                )

        # Sleep for a second to give the human players a chance to see how the
        # trick played out.
        time.sleep(1)
        self.send_game_state_to_client()

        # If this was not the last trick in the game then create a new trick
        # and restart this entire method.
        if Trick.objects.filter(deal=self.current_deal).count() < 13:
            self.new_trick()
            self.play()

        # If the last trick just finished then the game is over and a new deal
        # should be created followed by a new trick. For some reason, this
        # doesn't work as expected and sometimes freezes here. Need to dig
        # further to figure out what is happening.
        else:
            player_scores = sorted([
                (p, sum(c.score for c in Card.objects.filter(deal__game=self.game, trick__winning_player=p)))
                for p in self.game.players
            ], key=lambda x: x[1])
            if player_scores[-1][1] >= 100:
                winner, score = player_scores[0]
                self.game.winning_player = winner
                self.game.save()
                logger.info(f'Game over: Player {self.game.get_player_index(winner.id)} wins with a score of {score}')
                for player in self.game.players:
                    notification_text = 'Game Over. '
                    if player == winner:
                        notification_text += 'You win!'
                    else:
                        notification_text += f'{winner.name} wins.'
                    self.send_player_notification(
                        player=player,
                        notification=notification_text,
                    )
            else:
                logger.info('Deal over, starting next deal')
                self.new_deal()
                self.new_trick()
                self.play()
        self.send_game_state_to_client()

    def set_cards_to_pass(self, cards: list[Card]) -> None:
        """
        Mark which cards a player is going to pass.

        Because passing cards is asynchronous unlike playing cards which is
        synchronous, we must split passing into two steps:
        1. Each player signifies which cards they are going to pass.
        2. We pass all cards at the same time.

        This method is the first step and the `pass_cards` method is the second
        step.
        """
        # Validate the current deal hasn't passed yet.
        if self.current_deal.has_passed:
            logger.info('Skipping passing: Already passed this deal')
            return

        # Check if passing is necessary. On every 4th round we skip passing.
        direction = self.get_pass_direction()
        if direction is None:
            self.current_deal.has_passed = True
            self.current_deal.save()
            logger.info('Skipping passing: No passing this deal')
            return

        # Validate the correct number of cards are getting passed.
        if len(cards) != 3:
            logger.info(f'Skipping passing: {len(cards)} given; expected 3')
            return

        for card in cards:
            card.to_pass = True
            card.save()

        logger.info(f'Player {self.game.get_player_index(cards[0].player_id)} set 3 cards to pass')

    def pass_cards(self) -> None:
        """
        Pass cards to adjacent players.

        This happens at the start of the round. Right now bots will pass three
        random cards.
        """
        deal = self.current_deal
        direction = self.get_pass_direction()
        if direction is None:
            deal.has_passed = True
            deal.save()
            logger.info('Skipping passing on 4th deal')
            return

        for player in self.game.players:
            cards_to_pass = Card.objects.filter(
                player=player,
                deal=deal,
                to_pass=True,
            ).count()
            if cards_to_pass != 3:
                if not player.bot:
                    logger.info(f'Waiting for player {self.game.get_player_index(player.id)} to pass')
                    return

                cards = self.get_bot_cards_to_pass(player)
                self.set_cards_to_pass(cards)

        pass_map = {
            self.game.player_1_id: {
                'left': self.game.player_2,
                'right': self.game.player_4,
                'top': self.game.player_3,
            },
            self.game.player_2_id: {
                'left': self.game.player_3,
                'right': self.game.player_1,
                'top': self.game.player_4,
            },
            self.game.player_3_id: {
                'left': self.game.player_4,
                'right': self.game.player_2,
                'top': self.game.player_1,
            },
            self.game.player_4_id: {
                'left': self.game.player_1,
                'right': self.game.player_3,
                'top': self.game.player_2,
            },
        }

        for player in self.game.players:
            receiving_player = pass_map[player.id][direction]
            Card.objects.filter(
                deal=self.current_deal,
                player=player,
                to_pass=True,
            ).update(
                player=receiving_player,
                to_pass=False,
            )

        deal.has_passed = True
        deal.save()
        logger.info('Passing complete')

    def get_pass_direction(self) -> Optional[str]:
        """
        Determine what direction players are passing.

        Passing goes like this:
        - First hand -> Pass left
        - Second hand -> Pass right
        - Third hand -> Pass forward
        - Fourth hand -> Don't pass
        - Repeat sequence...
        """
        deal_number = Deal.objects.filter(
            game=self.game,
        ).count()
        return [
            'left',
            'right',
            'top',
            None,
        ][(deal_number - 1) % 4]

    def play_card(self, card: Card) -> None:
        """
        Play a card from a hand to the current trick.

        This method is used for both bots and human players. It will determine
        if a move is valid and if so it will add the card to the current trick.

        If the move is invalid (i.e. not following suit when you can) then the
        function will just log a message and return. We should implement
        something to actually give feedback to the user about why their move
        was invalid.

        Args:
             card (Card): The Card object to play on the current trick.
        """
        trick = self.current_trick

        # As mentioned in the docstring, return if the card is not a valid
        # move.
        if not self.is_valid_move(card):
            return

        # If this is the first card in the trick to be played then set it as
        # the first card on the trick object.
        if not Card.objects.filter(trick=trick).exists():
            trick.first_card = card
            trick.save()

        # "Play" the card.
        card.trick = trick
        card.save()

        logger.info(f'Player {self.game.get_player_index(card.player_id)} plays card {card.value}{card.suit}')

        # Sleep for a bit otherwise the bots move too fast.
        time.sleep(0.2)

    def is_valid_move(self, card: Card) -> bool:
        """
        Determine if a given card can be played right now.

        This method is called right before a card is to be played. We need to
        make sure the card about to be played follows the rules of the game:
        - Only play when it's the correct turn.
        - Follow suit if possible
        - Lead first trick with 2 of clubs
        - Can't play hearts or queen of spades on first trick
        - Can't lead with a heart until they've been broken

        Args:
            card (Card): The Card object to check if can be played now.

        Returns:
            True of card can be played; False if card cannot be played.
        """
        # Card is from a player trying to play out of turn.
        current_turn = self.get_current_turn()
        if not current_turn or current_turn != card.player:
            print(f'Invalid move: Wrong turn, {current_turn=} player={card.player}')
            return False

        # Tried to play out-of-suit when the player has an in-suit card.
        first_card = self.current_trick.first_card
        if first_card:
            if card.suit != first_card.suit:
                has_suited_card = Card.objects.filter(
                    suit=first_card.suit,
                    deal=self.current_deal,
                    trick__isnull=True,
                    player=card.player,
                ).exists()
                if has_suited_card:
                    print('Invalid move: Must play in-suit card')
                    return False

        is_first_trick = not Trick.objects.filter(
            deal=self.current_deal,
        ).exclude(id=self.current_trick.id).exists()
        if is_first_trick:
            # Trying to play hearts on first trick.
            if card.suit == Card.Suit.HEARTS:
                print('Invalid move: Can\'t start game with Heart')
                return False
            # Trying to play queen of spades on first trick.
            if card.suit == Card.Suit.SPADES and card.value == 12:
                print('Invalid move: Can\'t start game with Queen of Spades')
                return False

        # Force player to play 2 of clubs on first card of the first trick.
        if is_first_trick and not first_card:
            if card.suit != Card.Suit.CLUBS or card.value != 2:
                print('Invalid move: First trick must lead with 2 of clubs')
                return False

        # Check if hearts have been broken. The only exception here is if the
        # player only has hearts in their hand.
        if not first_card and card.suit == Card.Suit.HEARTS:
            is_hearts_broken = Card.objects.filter(
                suit=Card.Suit.HEARTS,
                deal=self.current_deal,
                trick__isnull=False,
            ).exists()
            if not is_hearts_broken:
                has_non_hearts = Card.objects.filter(
                    deal=self.current_deal,
                    trick__isnull=True,
                    player=card.player,
                ).exclude(
                    suit=Card.Suit.HEARTS,
                ).exists()
                if has_non_hearts:
                    print('Invalid move: Can\'t play hearts until broken')
                    return False

        # If none of the checks caught a bad move then we assume the move must
        # be good.
        return True

    def get_game_state(self, player: Player, is_observer: bool = False) -> dict:
        """
        Get the derived state of a Game at the current moment.

        This method drives the front end. We pull all the data we've stored
        about the game and translate it into a dictionary the front end can
        easily use.

        Returns:
            {
                game_id (str): UUID of Game object.
                trick_suit (str): Suit of first card played in current suit.
                is_observer (bool): True if player has joined to just watch.
                current_turn_relative_position (bottom|left|top|right): The position
                    of the current turn player relative to the requesting player.
                    This is used to display which player's turn it is.
                trick: {
                    bottom: {
                        suit (str): Suit of card played by the bottom player.
                        value (int): Value of card played by the bottom player.
                    },
                    left: {}
                    ...
                },
                player_bottom: {
                    player_id (str): UUID of Player object.
                    is_turn (bool): True if requesting player's turn else false.
                    relative_position (str(bottom)): Position of this player relative
                        to the requesting player.
                    absolute_position (int): Position of the player as they
                        joined the game.
                    hand: [
                        {
                            id (str): UUID of Card object.
                            suit (str): Suit of card.
                            value (str): Value of card.
                        }
                    ]
                }
            }
        """
        # Initialize state with static values.
        game_state = {
            'game_id': str(self.game.id),
            'player_id': str(player.id),
            'trick': {},
            'current_turn_relative_position': None,
            'is_observer': is_observer,
        }

        current_deal = self.current_deal
        current_trick = self.current_trick

        # Determine next action required by player.
        if not current_deal:
            action = 'deal-cards'
        elif not current_deal.has_passed:
            action = 'pass-cards'
        else:
            action = 'play-card'
        game_state['action'] = action

        # Check if passing has occurred already.
        if current_deal:
            game_state['has_passed'] = current_deal.has_passed
        else:
            game_state['has_passed'] = None

        # Determine the players absolute and relative positions.
        player_index = self.game.get_player_index(player.id)
        player_positions = ['bottom', 'left', 'top', 'right']
        player_position_map = {
            index: player_positions[(index + (4 - player_index)) % 4]
            for index in range(1, 5)
        }

        # Get the suit of the first card played in the suit if applicable.
        game_state['trick_suit'] = None
        if current_trick and current_trick.first_card:
            game_state['trick_suit'] = current_trick.first_card.suit

        current_turn = self.get_current_turn()

        # Loop through each player and fill out the state for them individually.
        for absolute_pos, relative_pos in player_position_map.items():
            # Get the cards currently in the players hand.
            current_player = getattr(self.game, f'player_{absolute_pos}')
            hand = []
            if current_deal:
                cards = Card.objects.filter(
                    player=current_player,
                    deal=current_deal,
                    trick__isnull=True,
                )
                cards = sorted(list(cards), key=lambda x: x.sort_key)
                hand = [
                    {
                        'id': str(card.id),
                        'suit': card.suit,
                        'value': card.value,
                    }
                    for card in cards
                ]

            # Update the top-level current turn value if it's this players turn.
            is_turn = current_player == current_turn
            if is_turn:
                game_state['current_turn_relative_position'] = relative_pos

            # Add player's state to the top-level dict.
            game_state[f'player_{relative_pos}'] = {
                'player_id': str(current_player.id),
                'relative_position': relative_pos,
                'absolute_position': absolute_pos,
                'is_turn': is_turn,
                'hand': hand,
            }

            # Lastly, update the trick with this player's card if they've
            # played on this trick already.
            if current_trick:
                card_played = Card.objects.filter(
                    trick=current_trick,
                    player=current_player,
                ).last()
                card = None
                if card_played:
                    card = {
                        'suit': card_played.suit,
                        'value': card_played.value,
                    }
                game_state['trick'][relative_pos] = card

        if self.game.winning_player:
            game_state['trick'] = {}

        return game_state

    def new_deal(self) -> Deal:
        """
        Create and start a new deal.

        This not only create a new Deal object but also creates a new deck of
        cards, shuffles it, and deals it.

        Returns:
            Newly created Deal object.
        """
        # Create Deal.
        deal = Deal.objects.create(game=self.game)
        logger.info('Created new Deal')

        # Create new deck of Cards.
        cards = []
        for suit in Card.Suit:
            for value in range(1, 14):
                card = Card.objects.create(
                    deal=deal,
                    suit=suit,
                    value=value,
                )
                cards.append(card)

        # Shuffle cards.
        random.shuffle(cards)

        # Deal cards.
        players = self.game.players
        for index, card in enumerate(cards):
            card.player = players[index % len(players)]
            card.save()
            self.send_game_state_to_client()

        logger.info('Shuffled and dealt')
        return deal

    def new_trick(self) -> Optional[Trick]:
        """
        Create new trick.

        Returns:
             Newly created Trick object or None if the Trick wasn't created for
                some reason.
        """
        deal = self.current_deal
        if not deal:
            return

        try:
            latest_trick = Trick.objects.filter(
                deal=deal,
            ).latest('created_at')
        except Trick.DoesNotExist:
            pass
        else:
            if latest_trick.winning_player is None:
                return

        # Create and return new Trick.
        trick = Trick.objects.create(deal=deal)
        logger.info('Created new trick')
        return trick

    def get_current_turn(self) -> Optional[Player]:
        """
        Get the player whose turn it currently is.

        This method basically follows the simple rules to determine who should
        go next. If for some reason this method can't determine who should
        go next, None will be returned. This method needs to be updated to not
        ever return None because logically it never makes sense for it to be
        nobody's turn.

        Returns:
            Player who should play next.
        """
        if not self.current_deal or not self.current_deal.has_passed:
            return None

        cards_played = Card.objects.filter(
            trick=self.current_trick,
        )

        # If no cards have been played in current trick, then it's the turn of
        # the winner of the last trick.
        if cards_played.count() == 0:
            last_trick = Trick.objects.filter(
                deal=self.current_deal,
            ).exclude(
                id=self.current_trick.id,
            ).order_by('created_at').last()
            if last_trick:
                return last_trick.winning_player

            # If this is the first card of the first trick, then the player who
            # has the 2 of clubs will start.
            two_of_clubs = Card.objects.get(
                deal=self.current_deal,
                value=2,
                suit=Card.Suit.CLUBS,
                trick__isnull=True,
            )
            return two_of_clubs.player

        # If a card has already been played then determine the next player in
        # a clockwise rotation.
        players_played = [
            self.game.get_player_index(card.player_id)
            for card in cards_played
        ]
        for i in [1, 2, 3, 4]:
            if i in players_played:
                for j in [(n + i - 1) % 4 + 1 for n in range(1, 5)]:
                    if j not in players_played:
                        return getattr(self.game, f'player_{j}')

    def get_bot_cards_to_pass(self, player: Player) -> list[Card]:
        """Interface with bot to determine cards to pass."""
        BotImplementation = get_bot_from_strategy(player.bot_strategy)
        bot = BotImplementation(player, self.game)
        return bot.get_cards_to_pass()

    def get_bot_card_to_play(self, player: Player) -> Card:
        """Interface with bot to determine card to play."""
        BotImplementation = get_bot_from_strategy(player.bot_strategy)
        bot = BotImplementation(player, self.game)
        return bot.get_card_to_play()

    @property
    def current_deal(self) -> Optional[Deal]:
        """Get and store current deal in memory."""
        try:
            return Deal.objects.filter(
                game=self.game,
            ).latest('created_at')
        except Deal.DoesNotExist:
            return None

    @property
    def current_trick(self) -> Optional[Trick]:
        """Get and store current trick in memory."""
        try:
            return Trick.objects.filter(
                deal=self.current_deal,
            ).latest('created_at')
        except Trick.DoesNotExist:
            return None

    def send_player_notification(
            self,
            player: Player,
            notification: str,
    ) -> None:
        """Send a notification to a specific player in the game player."""
        channel_layer = get_channel_layer()
        group = f'game_{self.game.id}_player_{player.id}'
        async_to_sync(channel_layer.group_send)(
            group,
            {
                'type': 'send_payload',
                'action': 'notify-user',
                'payload': {
                    'text': notification,
                },
            },
        )

    def send_game_state_to_client(self) -> None:
        """Send the game state to all players via websockets."""
        channel_layer = get_channel_layer()
        for player in self.game.players:
            group = f'game_{self.game.id}_player_{player.id}'
            game_state = self.get_game_state(player)
            async_to_sync(channel_layer.group_send)(
                group,
                {
                    'type': 'send_payload',
                    'action': 'update-game-state',
                    'payload': game_state,
                },
            )
