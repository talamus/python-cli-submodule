import sys
import os.path
import logging
import logging.handlers
import pprint
import textwrap
import pathlib
from typing import Any
from colorama import Fore, Style
from pythonjsonlogger import jsonlogger

VERBOSITY = {
    "NONE": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

_screen_logging_handler = None
_file_logging_handler = None


class ScreenFormatter(logging.Formatter):
    """A screen friendly version of the log record."""

    level_colors = (
        Style.BRIGHT + Fore.WHITE,  # NOTSET=0
        Style.BRIGHT + Fore.CYAN,  # DEBUG=10
        Style.BRIGHT + Fore.GREEN,  # INFO=20
        Style.BRIGHT + Fore.YELLOW,  # WARN=30
        Style.BRIGHT + Fore.RED,  # ERROR=40
        Style.BRIGHT + Fore.MAGENTA,  # CRITICAL=50
    )
    additional_info_color = Fore.LIGHTWHITE_EX
    reset_colors = Style.RESET_ALL

    def __init__(self, *args, **kwargs):
        # Disable colors if stdout is being redirected
        if not sys.stdout.isatty():
            ScreenFormatter.level_colors = (
                "[!!!]   ",
                "[DEBUG] ",
                "[INFO]  ",
                "[WARNING] ",
                "[ERROR] ",
                "[CRITICAL] ",
            )
            ScreenFormatter.additional_info_color = ""
            ScreenFormatter.reset_colors = ""
        super().__init__(*args, **kwargs)

    def format(self, record):
        level = record.levelno // 10
        level = level if level < len(ScreenFormatter.level_colors) else 0
        level_color = ScreenFormatter.level_colors[level]

        args = record.args
        args = args if isinstance(args, tuple) else [args]

        msg = str(record.msg)
        additional_info = ""
        # Wrap and print the final argument beautifully
        if msg.endswith(" %s"):
            info = args[-1]
            args = args[:-1]
            msg = msg[:-3]
            wrapped_info = (
                "\n".join(textwrap.wrap(info))
                if isinstance(info, str)
                else pprint.pformat(info)
            )
            additional_info = (
                "\n\n"
                + ScreenFormatter.additional_info_color
                + textwrap.indent(wrapped_info, "  ")
                + ScreenFormatter.reset_colors
                + "\n"
            )

        return level_color + msg % args + ScreenFormatter.reset_colors + additional_info


def set_up_loggers(cfg: dict[str, Any] = None) -> None:
    global _screen_logging_handler
    global _file_logging_handler

    if cfg is None:
        cfg = {"verbosity": "ERROR"}

    # Each handler handles the filtering
    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    # Screen output (a.k.a Verbosity/Quiet)
    if not _screen_logging_handler:
        _screen_logging_handler = logging.StreamHandler(sys.stdout)
        _screen_logging_handler.setFormatter(ScreenFormatter())
        logger.addHandler(_screen_logging_handler)

    _screen_logging_handler.setLevel(VERBOSITY[cfg["verbosity"]])

    # Logging to a log file
    if "log_file" in cfg and cfg["log_file"]:
        if not _file_logging_handler:
            # Try to create the log dir
            log_dir, _ = os.path.split(cfg["log_file"])
            pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)

            # Rotate logs either by time...
            if "log_when_to_rotate" in cfg:
                _file_logging_handler = logging.handlers.TimedRotatingFileHandler(
                    cfg["log_file"],
                    when=cfg["log_when_to_rotate"],
                    backupCount=cfg["log_max_files"],
                )

            # ...or by file size
            else:
                _file_logging_handler = logging.handlers.RotatingFileHandler(
                    cfg["log_file"],
                    maxBytes=cfg["log_max_bytes"],
                    backupCount=cfg["log_max_files"],
                )

            _file_logging_handler.setFormatter(
                jsonlogger.JsonFormatter(
                    "%(asctime)s %(levelname)s %(name)s %(message)s"
                )
            )
            logger.addHandler(_file_logging_handler)

        if "log_level" in cfg and cfg["log_level"]:
            _file_logging_handler.setLevel(VERBOSITY[cfg["log_level"]])
