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

# Headers and colors when printing directly to a terminal
TTY_LEVEL_HEADERS = {
    "DEBUG": "",
    "INFO": "",
    "WARN": "",
    "ERROR": "",
    "CRITICAL": "",
}
TTY_LEVEL_COLORS = {
    "DEBUG": Style.BRIGHT + Fore.CYAN,
    "INFO": Style.BRIGHT + Fore.GREEN,
    "WARN": Style.BRIGHT + Fore.YELLOW,
    "ERROR": Style.BRIGHT + Fore.RED,
    "CRITICAL": Style.BRIGHT + Fore.MAGENTA,
}
TTY_ARGUMENT_COLOR = Fore.LIGHTWHITE_EX
TTY_EXTRA_FIELDS_COLOR = Fore.LIGHTWHITE_EX
TTY_RESET_COLORS = Style.RESET_ALL

# Headers and colors when `stdout` is being redirected
REDIRECTED_LEVEL_HEADERS = {
    "DEBUG": "[DEBUG] ",
    "INFO": "[INFO]  ",
    "WARN": "[WARNING] ",
    "ERROR": "[ERROR] ",
    "CRITICAL": "[CRITICAL] ",
}
REDIRECTED_LEVEL_COLORS = {
    "DEBUG": "",
    "INFO": "",
    "WARN": "",
    "ERROR": "",
    "CRITICAL": "",
}
REDIRECTED_ARGUMENT_COLOR = ""
REDIRECTED_EXTRA_FIELDS_COLOR = ""
REDIRECTED_RESET_COLORS = ""


_screen_logging_handler = None
_file_logging_handler = None


class ScreenFormatter(jsonlogger.JsonFormatter):
    """A screen friendly version of the log formatter."""

    def __init__(self, *args, **kwargs):
        if sys.stdout.isatty():
            self.LEVEL_HEADERS = TTY_LEVEL_HEADERS
            self.LEVEL_COLORS = TTY_LEVEL_COLORS
            self.ARGUMENT_COLOR = TTY_ARGUMENT_COLOR
            self.EXTRA_FIELDS_COLOR = TTY_EXTRA_FIELDS_COLOR
            self.RESET_COLORS = TTY_RESET_COLORS
        else:
            self.LEVEL_HEADERS = REDIRECTED_LEVEL_HEADERS
            self.LEVEL_COLORS = REDIRECTED_LEVEL_COLORS
            self.ARGUMENT_COLOR = REDIRECTED_ARGUMENT_COLOR
            self.EXTRA_FIELDS_COLOR = REDIRECTED_EXTRA_FIELDS_COLOR
            self.RESET_COLORS = REDIRECTED_RESET_COLORS
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
                + self.EXTRA_FIELDS_COLOR
                + "\n".join(extra_fields)
                + self.RESET_COLORS
            )

        return (
            self.LEVEL_HEADERS[levelname]
            + self.LEVEL_COLORS[levelname]
            + message
            + (":" if stringified_extra_fields else "")
            + self.RESET_COLORS
            + stringified_extra_fields
        )

    def format(self, record):
        """Formatting a record. Highlighting possible arguments."""
        record = logging.makeLogRecord(vars(record))
        record.msg = record.msg.replace(
            "%s",
            self.RESET_COLORS
            + self.ARGUMENT_COLOR
            + "%s"
            + self.RESET_COLORS
            + self.LEVEL_COLORS[record.levelname],
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

    # Default configuration
    cfg = cfg or {"verbosity": "ERROR"}

    # Each handler handles the filtering separately
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
