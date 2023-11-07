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

LOG_FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

VERBOSITY = {
    "NONE": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

_screen_logging_handler = None
_file_logging_handler = None


class ScreenFormatter(jsonlogger.JsonFormatter):
    """A screen friendly version of the log formatter."""

    level_headers = {
        "DEBUG": "",
        "INFO": "",
        "WARN": "",
        "ERROR": "",
        "CRITICAL": "",
    }

    level_colors = {
        "DEBUG": Style.BRIGHT + Fore.CYAN,
        "INFO": Style.BRIGHT + Fore.GREEN,
        "WARN": Style.BRIGHT + Fore.YELLOW,
        "ERROR": Style.BRIGHT + Fore.RED,
        "CRITICAL": Style.BRIGHT + Fore.MAGENTA,
    }
    argument_color = Fore.LIGHTWHITE_EX
    extra_fields_color = Fore.LIGHTWHITE_EX
    reset_colors = Style.RESET_ALL

    def __init__(self, *args, **kwargs):
        # Disable colors if stdout is being redirected
        if not sys.stdout.isatty():
            ScreenFormatter.level_colors = ScreenFormatter.level_headers
            ScreenFormatter.level_headers = {
                "DEBUG": "[DEBUG] ",
                "INFO": "[INFO]  ",
                "WARN": "[WARNING] ",
                "ERROR": "[ERROR] ",
                "CRITICAL": "[CRITICAL] ",
            }
            ScreenFormatter.argument_color = ""
            ScreenFormatter.extra_fields_color = ""
            ScreenFormatter.reset_colors = ""
        super().__init__(*args, **kwargs)

    def jsonify_log_record(self, log_record):
        """We are piggybacking the JsonFormatter to easily get the extra fields..."""
        levelname = log_record.pop("levelname")
        message = log_record.pop("message")
        if "exc_info" in log_record:
            del log_record["exc_info"]

        def format_extra_field(name, value):
            if not isinstance(value, str):
                value = pprint.pformat(value, sort_dicts=False)
            value = textwrap.indent(value, (len(name) + 2) * " ").strip()
            return textwrap.indent(f"{name}: {value}", "  ") + "\n"

        extra_fields = []
        for key, value in log_record.items():
            extra_fields.append(format_extra_field(key, value))

        stringified_extra_fields = ""
        if extra_fields:
            stringified_extra_fields = (
                "\n\n"
                + ScreenFormatter.extra_fields_color
                + "\n".join(extra_fields)
                + ScreenFormatter.reset_colors
            )

        return (
            ScreenFormatter.level_headers[levelname]
            + ScreenFormatter.level_colors[levelname]
            + message
            + (":" if stringified_extra_fields else "")
            + ScreenFormatter.reset_colors
            + stringified_extra_fields
        )

    def format(self, record):
        """Formatting a record. Highlighting possible arguments."""
        record = logging.makeLogRecord(vars(record))
        record.msg = record.msg.replace(
            "%s",
            ScreenFormatter.reset_colors
            + ScreenFormatter.argument_color
            + "%s"
            + ScreenFormatter.reset_colors
            + ScreenFormatter.level_colors[record.levelname],
        )
        return super().format(record)


def set_up_loggers(cfg: dict[str, Any] = None) -> None:
    """
    Initialize loggers according to the configuration.

    If no configuration is provided, an error logging cabable
    screen logger is initialized.
    """
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
        _screen_logging_handler.setFormatter(
            ScreenFormatter("%(levelname)s %(message)s")
        )
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
                jsonlogger.JsonFormatter(cfg["log_file_format"])
            )
            logger.addHandler(_file_logging_handler)

        if "log_level" in cfg and cfg["log_level"]:
            _file_logging_handler.setLevel(VERBOSITY[cfg["log_level"]])
