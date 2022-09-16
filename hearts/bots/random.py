import random

from hearts.bots.base import BaseBot
from hearts.models import Card


class RandomBot(BaseBot):
    """Bot that picks cards at random."""

    def get_cards_to_pass(self) -> list[Card]:
        """
        Determine which cards should be passed at the start of the game.

        Choose 3 random cards.
        """
        cards = self.get_cards()
        return list(cards.filter(
            trick__isnull=True,
            to_pass=False,
        ).order_by('?')[:3])

    def get_card_to_play(self) -> Card:
        """
        Determine which card should be played next.

        Choose random, as long as it follows the rules.
        """
        cards = self.get_cards()
        eligible_cards = list(cards.filter(trick__isnull=True))

        # If the bot has a card in the correct suit, play a random card in
        # that suit.
        if first_card_of_trick := self.current_trick.first_card:
            eligible_cards_in_suit = [
                c for c in eligible_cards
                if c.suit == first_card_of_trick.suit
            ]
            eligible_cards = eligible_cards_in_suit or eligible_cards

        else:
            # If the bot has the two of clubs, they should play it.
            for card in eligible_cards:
                if card.suit == Card.Suit.CLUBS and card.value == 2:
                    return card

        # Pick randomly from eligible cards.
        return random.choice(eligible_cards)
