import logging
import random
from typing import Type

from hearts.bots.base import Bot
from hearts.bots.random import RandomBot
from hearts.bots.lowest import LowestBot

logger = logging.getLogger('django')


class BotStrategy:
    """
    Constant for storing strategy types.

    Add new strategies to this list as well as the `BOT_CLASS_MAP`.
    """
    RANDOM = 'random'
    LOWEST = 'lowest'


BOT_CLASS_MAP = {
    BotStrategy.RANDOM: RandomBot,
    BotStrategy.LOWEST: LowestBot,
}


def get_bot_from_strategy(strategy: str) -> Type[Bot]:
    """
    Given a strategy, return the Bot class to be used in game.

    If a bot strategy is missing or invalid, a random strategy will be chosen.
    """
    if strategy not in BOT_CLASS_MAP:
        random_strategy = random.choice(list(BOT_CLASS_MAP.keys()))
        logger.error(
            f'Bot strategy not defined: {strategy}; '
            f'Using strategy: {random_strategy}'
        )
        strategy = random_strategy

    return BOT_CLASS_MAP[strategy]
