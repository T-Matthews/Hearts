from uuid import uuid4

from django.db import models


class Trick(models.Model):
    """
    Representation of a single trick in a deal.

    A deal has many tricks. A trick has many cards.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)

    deal = models.ForeignKey(
        'hearts.Deal',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tricks',
    )

    winning_player = models.ForeignKey(
        'hearts.Player',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tricks_won',
    )

    first_card = models.ForeignKey(
        'hearts.Card',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tricks_as_first_card',
    )

    created_at = models.DateTimeField(auto_now=True)
