from abc import ABC, abstractmethod
from typing import TypeVar

from django.db.models import QuerySet

from hearts.models import Card, Deal, Game, Player, Trick

Bot = TypeVar('Bot', bound='BaseBot')


class BaseBot(ABC):
    """Abstract Base Class for all bots."""

    def __init__(self, player: Player, game: Game):
        self.player = player
        self.game = game

    @abstractmethod
    def get_cards_to_pass(self) -> list[Card]:
        """Determine which cards should be passed at the start of the game."""
        pass

    @abstractmethod
    def get_card_to_play(self) -> Card:
        """Determine which card should be played next."""
        pass

    def get_cards(self) -> QuerySet:
        """Get QuerySet of bot's cards this deal."""
        return Card.objects.filter(
            player=self.player,
            deal=self.current_deal,
        )

    @property
    def current_deal(self) -> Deal:
        """Get the current deal."""
        return Deal.objects.filter(
            game=self.game,
        ).latest('created_at')

    @property
    def current_trick(self) -> Trick:
        """Get the current trick."""
        return Trick.objects.filter(
            deal=self.current_deal,
        ).latest('created_at')
