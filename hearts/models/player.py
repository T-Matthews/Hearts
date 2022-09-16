from uuid import uuid4

from django.db import models


class Player(models.Model):
    """
    Users and bots who participate in games.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)

    name = models.TextField()

    bot = models.BooleanField(default=False)

    bot_strategy = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now=True)
