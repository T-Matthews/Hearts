from hearts.bots.base import BaseBot
from hearts.models import Card


class LowestBot(BaseBot):
    """Bot that trys to play the lowest cards."""

    def get_cards_to_pass(self) -> list[Card]:
        """
        Determine which cards should be passed at the start of the game.

        Tries to get rid of the 3 highest cards.
        """
        cards = self.get_cards()
        return list(cards.filter(
            trick__isnull=True,
            to_pass=False,
        ).order_by('-value')[:3])

    def get_card_to_play(self) -> Card:
        """
        Determine which card should be played next.

        Will try to play the lowest card unless the bot can't follow suit. In
        that case the bot will play it's highest card.
        """
        cards = self.get_cards()
        eligible_cards = list(cards.filter(trick__isnull=True).order_by('value'))
        eligible_cards.sort(key=lambda x: x.value if x.value > 1 else 99)

        # If the bot has a card in the correct suit, play the lowest one.
        if first_card_of_trick := self.current_trick.first_card:
            eligible_cards_in_suit = [
                c for c in eligible_cards
                if c.suit == first_card_of_trick.suit
            ]
            if eligible_cards_in_suit:
                eligible_cards = eligible_cards_in_suit
            else:
                # If the bot does not have a card in the correct suit, play
                # the highest one.
                eligible_cards.sort(
                    key=lambda x: x.value if x.value > 1 else 99,
                    reverse=True,
                )

        else:
            # If the bot has the two of clubs, they should play it.
            for card in eligible_cards:
                if card.suit == Card.Suit.CLUBS and card.value == 2:
                    return card

            # Only pick hearts to start trick if hearts are broken.
            is_hearts_broken = Card.objects.filter(
                deal=self.current_deal,
                trick__isnull=False,
                suit=Card.Suit.HEARTS,
            ).exists()
            if not is_hearts_broken:
                eligible_cards = [
                    e for e in eligible_cards
                    if e.suit != Card.Suit.HEARTS
                ]

        return eligible_cards[0]
