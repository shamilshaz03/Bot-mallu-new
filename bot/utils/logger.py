import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)

logger = logging.getLogger("premium-bot")
