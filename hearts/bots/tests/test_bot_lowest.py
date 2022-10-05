from django.test import TestCase

from hearts.bots.lowest import LowestBot
from hearts.models import Card, Deal, Game, Player, Trick


class LowestBotTestCase(TestCase):

    def setUp(self):
        """
        Set up game state before each test.

        This function runs before each test, creating a new game and players.
        """
        super().setUp()

        # Set up a new game. First we need 4 players.
        self.bot = Player.objects.create(name='Test Bot', bot=True)
        self.human = Player.objects.create(name='Human player')
        self.other_bot_1 = Player.objects.create(name='Other Bot 1', bot=True)
        self.other_bot_2 = Player.objects.create(name='Other Bot 2', bot=True)

        # Create the game with 4 players as would normally happen when a game
        # is started.
        self.game = Game.objects.create(
            player_1=self.human,
            player_2=self.bot,
            player_3=self.other_bot_1,
            player_4=self.other_bot_2,

        )

        # Create the game's first deal and trick.
        self.current_deal = Deal.objects.create(game=self.game)
        self.current_trick = Trick.objects.create(deal=self.current_deal)

    def test_get_cards_to_pass(self):
        """Should pass the 3 cards with the highest value."""
        # Create and assign the bot 13 cards.
        cards = [
            (Card.Suit.HEARTS, 5),
            (Card.Suit.HEARTS, 7),
            (Card.Suit.HEARTS, 8),
            (Card.Suit.SPADES, 2),
            (Card.Suit.SPADES, 10),
            (Card.Suit.DIAMONDS, 3),
            (Card.Suit.DIAMONDS, 7),
            (Card.Suit.DIAMONDS, 8),
            (Card.Suit.DIAMONDS, 9),
            (Card.Suit.DIAMONDS, 12),
            (Card.Suit.CLUBS, 4),
            (Card.Suit.CLUBS, 7),
            (Card.Suit.CLUBS, 11),
        ]
        for suit, value in cards:
            Card.objects.create(
                player=self.bot,
                deal=self.current_deal,
                suit=suit,
                value=value,
            )

        # Given the hand we defined above, expect these 3 cards to be passed.
        expected_cards_to_pass = [
            Card.objects.get(player=self.bot, deal=self.current_deal, suit=Card.Suit.SPADES, value=10),
            Card.objects.get(player=self.bot, deal=self.current_deal, suit=Card.Suit.DIAMONDS, value=12),
            Card.objects.get(player=self.bot, deal=self.current_deal, suit=Card.Suit.CLUBS, value=11),
        ]

        # Call production code to get real results given this fake scenario.
        lowest_bot = LowestBot(player=self.bot, game=self.game)
        cards_to_pass = lowest_bot.get_cards_to_pass()

        # Sort both the real results and the expected results so we can compare.
        cards_to_pass.sort(key=lambda x: str(x))
        expected_cards_to_pass.sort(key=lambda x: str(x))

        # Assert both lists contain the same cards.
        self.assertEqual(cards_to_pass, expected_cards_to_pass)

    def test_get_card_to_play__two_of_clubs(self):
        """Should play the two of clubs if possible."""
        # Create and assign the bot 13 cards, including the 2 of clubs.
        cards = [
            (Card.Suit.HEARTS, 5),
            (Card.Suit.HEARTS, 7),
            (Card.Suit.HEARTS, 8),
            (Card.Suit.SPADES, 2),
            (Card.Suit.SPADES, 10),
            (Card.Suit.DIAMONDS, 3),
            (Card.Suit.DIAMONDS, 7),
            (Card.Suit.DIAMONDS, 8),
            (Card.Suit.DIAMONDS, 9),
            (Card.Suit.DIAMONDS, 12),
            (Card.Suit.CLUBS, 2),
            (Card.Suit.CLUBS, 7),
            (Card.Suit.CLUBS, 11),
        ]
        for suit, value in cards:
            Card.objects.create(
                player=self.bot,
                deal=self.current_deal,
                suit=suit,
                value=value,
            )

        # Call production code to get real results given this fake scenario.
        lowest_bot = LowestBot(player=self.bot, game=self.game)
        card_to_play = lowest_bot.get_card_to_play()

        # Assert the card to play is the 2 of clubs.
        self.assertEqual(card_to_play.suit, Card.Suit.CLUBS)
        self.assertEqual(card_to_play.value, 2)

    def test_get_card_to_play__follow_suit(self):
        """Should play the lowest card following suit if possible."""
        # Create and assign the bot 13 cards.
        cards = [
            (Card.Suit.HEARTS, 5),
            (Card.Suit.HEARTS, 7),
            (Card.Suit.HEARTS, 8),
            (Card.Suit.SPADES, 2),
            (Card.Suit.SPADES, 10),
            (Card.Suit.DIAMONDS, 3),
            (Card.Suit.DIAMONDS, 7),
            (Card.Suit.DIAMONDS, 8),
            (Card.Suit.DIAMONDS, 9),
            (Card.Suit.DIAMONDS, 12),
            (Card.Suit.CLUBS, 4),
            (Card.Suit.CLUBS, 7),
            (Card.Suit.CLUBS, 11),
        ]
        for suit, value in cards:
            Card.objects.create(
                player=self.bot,
                deal=self.current_deal,
                suit=suit,
                value=value,
            )

        # Set the first card played on the trick to be diamonds.
        first_card = Card.objects.create(
            player=self.human,
            deal=self.current_deal,
            suit=Card.Suit.DIAMONDS,
            value=10,
            trick=self.current_trick,
        )
        self.current_trick.first_card = first_card
        self.current_trick.save()

        # Call production code to get real results given this fake scenario.
        lowest_bot = LowestBot(player=self.bot, game=self.game)
        card_to_play = lowest_bot.get_card_to_play()

        # Assert the card to play is the 3 of diamonds (lowest diamond in hand).
        self.assertEqual(card_to_play.suit, Card.Suit.DIAMONDS)
        self.assertEqual(card_to_play.value, 3)

    def test_get_card_to_play__cant_follow_suit(self):
        """Should play the highest card not following suit if possible."""
        # Create and assign the bot cards but no diamonds.
        cards = [
            (Card.Suit.HEARTS, 5),
            (Card.Suit.HEARTS, 7),
            (Card.Suit.HEARTS, 8),
            (Card.Suit.SPADES, 2),
            (Card.Suit.SPADES, 10),
            (Card.Suit.CLUBS, 4),
            (Card.Suit.CLUBS, 7),
            (Card.Suit.CLUBS, 11),
        ]
        for suit, value in cards:
            Card.objects.create(
                player=self.bot,
                deal=self.current_deal,
                suit=suit,
                value=value,
            )

        # Set the first card played on the trick to be diamonds.
        first_card = Card.objects.create(
            player=self.human,
            deal=self.current_deal,
            suit=Card.Suit.DIAMONDS,
            value=10,
            trick=self.current_trick,
        )
        self.current_trick.first_card = first_card
        self.current_trick.save()

        # Call production code to get real results given this fake scenario.
        lowest_bot = LowestBot(player=self.bot, game=self.game)
        card_to_play = lowest_bot.get_card_to_play()

        # Assert the card to play is the 11 of clubs (highest card in hand).
        self.assertEqual(card_to_play.suit, Card.Suit.CLUBS)
        self.assertEqual(card_to_play.value, 11)

    def test_get_card_to_play__leads_with_lowest__hearts_unbroken(self):
        """Should play the highest card not following suit if possible."""
        # Create and assign the bot cards. Lowest is hearts but hearts have
        # not been broken.
        cards = [
            (Card.Suit.HEARTS, 2),
            (Card.Suit.HEARTS, 7),
            (Card.Suit.HEARTS, 8),
            (Card.Suit.SPADES, 6),
            (Card.Suit.SPADES, 10),
            (Card.Suit.DIAMONDS, 4),
            (Card.Suit.CLUBS, 7),
            (Card.Suit.CLUBS, 11),
        ]
        for suit, value in cards:
            Card.objects.create(
                player=self.bot,
                deal=self.current_deal,
                suit=suit,
                value=value,
            )

        # Call production code to get real results given this fake scenario.
        lowest_bot = LowestBot(player=self.bot, game=self.game)
        card_to_play = lowest_bot.get_card_to_play()

        # Assert the card to play is the 4 of diamonds (lowest card in hand, excluding hearts).
        self.assertEqual(card_to_play.suit, Card.Suit.DIAMONDS)
        self.assertEqual(card_to_play.value, 4)

    def test_get_card_to_play__leads_with_lowest__hearts_broken(self):
        """Should play the highest card not following suit if possible."""
        # Create and assign the bot cards.
        cards = [
            (Card.Suit.HEARTS, 2),
            (Card.Suit.HEARTS, 7),
            (Card.Suit.HEARTS, 8),
            (Card.Suit.SPADES, 6),
            (Card.Suit.SPADES, 10),
            (Card.Suit.DIAMONDS, 4),
            (Card.Suit.CLUBS, 7),
            (Card.Suit.CLUBS, 11),
        ]
        for suit, value in cards:
            Card.objects.create(
                player=self.bot,
                deal=self.current_deal,
                suit=suit,
                value=value,
            )

        # Another player has already played a heart on the previous trick.
        # Hearts are now broken.
        Card.objects.create(
            player=self.human,
            deal=self.current_deal,
            suit=Card.Suit.HEARTS,
            value=3,
            trick=self.current_trick,
        )
        self.current_trick = Trick.objects.create(deal=self.current_deal)

        # Call production code to get real results given this fake scenario.
        lowest_bot = LowestBot(player=self.bot, game=self.game)
        card_to_play = lowest_bot.get_card_to_play()

        # Assert the card to play is the 2 of hearts (lowest card in hand).
        self.assertEqual(card_to_play.suit, Card.Suit.HEARTS)
        self.assertEqual(card_to_play.value, 2)
