from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _


class Card(models.Model):
    """
    Representation of a single card in a deal.

    52 cards are created and assigned at the creation of each Deal. These
    objects represent both unplayed and played cards.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)

    player = models.ForeignKey(
        'hearts.Player',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    deal = models.ForeignKey(
        'hearts.Deal',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    trick = models.ForeignKey(
        'hearts.Trick',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Suit(models.TextChoices):
        HEARTS = 'h', _('Hearts')
        SPADES = 's', _('Spades')
        DIAMONDS = 'd', _('Diamonds')
        CLUBS = 'c', _('Clubs')

    suit = models.CharField(
        max_length=1,
        choices=Suit.choices,
    )

    value = models.IntegerField()

    to_pass = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now=True)

    @property
    def sort_key(self) -> int:
        base_value = {
            self.Suit.HEARTS: 100,
            self.Suit.SPADES: 200,
            self.Suit.DIAMONDS: 300,
            self.Suit.CLUBS: 400,
        }[self.suit]
        sort_key = base_value + self.value
        if self.value == 1:
            sort_key += 13
        return sort_key

    @property
    def score(self) -> int:
        if self.suit == self.Suit.SPADES and self.value == 12:
            return 13
        elif self.suit == self.Suit.HEARTS:
            return 1
        else:
            return 0

    def __str__(self) -> str:
        return f'{self.suit.upper()}{self.value}'
