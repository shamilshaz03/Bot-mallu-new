import math
from bot.config import config


def total_pages(total_items: int) -> int:
    return max(1, math.ceil(total_items / config.ITEMS_PER_PAGE))
