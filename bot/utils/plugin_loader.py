"""
Pyrogram's built-in plugin system (Client(plugins=dict(root=...))) will
still perform the actual handler registration — that part of the
architecture is unchanged. But Pyrogram's internal loader only *warns*
on a per-module import failure and otherwise carries on, which made it
easy for a broken plugin file to fail invisibly in production.

This module does an explicit pre-flight pass: it walks every .py file
under bot/plugins, imports it with importlib, and logs a clear
success/failure line for each one — with a full traceback on failure —
before the bot ever starts. Nothing here changes how handlers are
registered; it only makes failures impossible to miss.
"""
import importlib
import traceback
from pathlib import Path

from bot.utils.logger import logger


def verify_plugins(root: str = "bot/plugins") -> tuple[int, int, list[str]]:
    root_path = Path(root)
    if not root_path.exists():
        logger.error("Plugin root '%s' does not exist!", root)
        return 0, 0, [root]

    py_files = sorted(root_path.rglob("*.py"))
    py_files = [f for f in py_files if f.stem != "__init__"]

    succeeded, failed = 0, 0
    failed_modules: list[str] = []

    logger.info("---- Loading plugins from '%s' ----", root)

    for path in py_files:
        module_name = ".".join(path.with_suffix("").parts)
        try:
            importlib.import_module(module_name)
        except Exception:
            failed += 1
            failed_modules.append(module_name)
            logger.error("FAILED to load plugin '%s':\n%s", module_name, traceback.format_exc())
        else:
            succeeded += 1
            logger.info("Loaded plugin: %s", module_name)

    logger.info(
        "---- Plugin loading complete: %d succeeded, %d failed (of %d files) ----",
        succeeded, failed, len(py_files),
    )
    return succeeded, failed, failed_modules
