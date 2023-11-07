import sys
import os.path
import textwrap
import argparse
import yaml
import platformdirs

from .cli import main, VERBOSITY
from . import DEFAULT_CONFIG, some_code

# -----------------------------------------------------------------------------

APP_NAME = "some_module"
APP_DESCRIPTION = f"An example Command Line Interface of some module."
APP_CONFIG = {
    "config_file": os.path.join(
        platformdirs.user_config_dir(APP_NAME), f"{APP_NAME}.config"
    ),
    "verbosity": "ERROR",
    "log_file": os.path.join(platformdirs.user_log_dir(APP_NAME), f"{APP_NAME}.log"),
    "log_file_format": "%(asctime)s %(levelname)s %(name)s %(message)s",
    "log_level": "INFO",
    "log_max_bytes": 100 * 1024,
    "log_max_files": 10,
}
cfg = DEFAULT_CONFIG | APP_CONFIG
APP_USAGE = f"""
Here will be an example...

Default configuration:
{textwrap.indent(yaml.dump(cfg, sort_keys=False), "  ")}
"""

# -----------------------------------------------------------------------------

argparser = argparse.ArgumentParser(
    prog=f"python -m {APP_NAME}",
    description=APP_DESCRIPTION,
    epilog=APP_USAGE,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
argparser.add_argument(
    "paths",
    metavar="content",
    nargs="*",
    help="content to be processed",
)
argparser.add_argument(
    "-v",
    "--verbosity",
    action="count",
    default=0,
    help="set output verbosity (-v = INFO, -vv = DEBUG)",
)
argparser.add_argument(
    "-q",
    "--quiet",
    dest="verbosity",
    action="store_const",
    const=-1,
    help="Do not output anything",
)
argparser.add_argument(
    "--config",
    dest="alterative_config_file",
    metavar="CONFIG",
    help="read configuration from this file (YAML format)",
)
argparser.add_argument(
    "--loglevel",
    dest="log_level",
    metavar="LEVEL",
    choices=VERBOSITY.keys(),
    help=f"set logging level ({ ', '.join(list(VERBOSITY.keys())) })",
)
argparser.add_argument(
    "--dryrun",
    action="store_true",
    help="do not do anything",
)

args = vars(argparser.parse_args())

# Remove arguments that are not set
if not args["log_level"]:
    del args["log_level"]
if not args["dryrun"]:
    del args["dryrun"]

sys.exit(main(lambda cfg: some_code(cfg=cfg), args, cfg, f"Starting {APP_NAME}..."))
