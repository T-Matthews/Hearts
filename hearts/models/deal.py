from uuid import uuid4

from django.db import models


class Deal(models.Model):
    """
    Representation of a single deal in a game.

    A game has many deals. A Deal has many tricks.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)

    game = models.ForeignKey(
        'hearts.Game',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='deals',
    )

    created_at = models.DateTimeField(auto_now=True)
