from typing import Optional
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

    @property
    def players(self) -> list:
        """Access game players as a list."""
        return [
            self.player_1,
            self.player_2,
            self.player_3,
            self.player_4,
        ]

    def get_player_index(self, player_id: str) -> Optional[int]:
        """
        Get the Player's absolute position in the game given their ID.

        Returns:
            Number 1-4 if player is in game else None.
        """
        return {
            self.player_1_id: 1,
            self.player_2_id: 2,
            self.player_3_id: 3,
            self.player_4_id: 4,
        }.get(player_id)
