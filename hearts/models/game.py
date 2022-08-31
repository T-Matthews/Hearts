from uuid import uuid4

from django.db import models


class Game(models.Model):
    """
    Representation of an entire game.

    A game has many deals.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)

    player_1 = models.ForeignKey(
        'hearts.Player',
        on_delete=models.CASCADE,
        related_name='games_as_player_1',
    )

    player_2 = models.ForeignKey(
        'hearts.Player',
        on_delete=models.CASCADE,
        related_name='games_as_player_2',
    )

    player_3 = models.ForeignKey(
        'hearts.Player',
        on_delete=models.CASCADE,
        related_name='games_as_player_3',
    )

    player_4 = models.ForeignKey(
        'hearts.Player',
        on_delete=models.CASCADE,
        related_name='games_as_player_4',
    )

    winning_player = models.ForeignKey(
        'hearts.Player',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='games_won',
    )

    created_at = models.DateTimeField(auto_now=True)
