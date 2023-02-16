import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

import yaml

HOME = pathlib.Path.home()
TOP_CONFIGDIR = pathlib.Path(HOME, pathlib.Path(".config"))
CONFIG_DIR = pathlib.Path(TOP_CONFIGDIR, pathlib.Path("app-ads"))
LOG_DIR = pathlib.Path(CONFIG_DIR, pathlib.Path("logs"))
MODULE_DIR = pathlib.Path(__file__).resolve().parent.parent


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def check_config_dirs():
    dirs = [TOP_CONFIGDIR, CONFIG_DIR, LOG_DIR]
    for dir in dirs:
        if not pathlib.Path.exists(dir):
            pathlib.Path.mkdir(dir, exist_ok=True)


def get_logger(mod_name: str, log_name: str = "dash"):
    format = "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
    check_config_dirs()
    log_dir = pathlib.Path(HOME, pathlib.Path(".config/app-ads/logs"))
    if not pathlib.Path.exists(log_dir):
        pathlib.Path.mkdir(log_dir, exist_ok=True)
        print(f"Couldn't find {log_dir=} so it was created.")
    filename = f"{log_dir}/{log_name}.log"
    # Writes to file
    rotate_handler = RotatingFileHandler(
        filename=filename, maxBytes=50000000, backupCount=5
    )
    logging.basicConfig(
        format=format,
        level=logging.INFO,
        handlers=[
            rotate_handler,
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(mod_name)
    return logger


# Set global handling of uncaught exceptions
sys.excepthook = handle_exception

logger = get_logger(__name__)

DATE_FORMAT = "%Y-%m-%d"

CONFIG_FILENAME = "config.yml"

CONFIG_FILE_PATH = pathlib.Path(CONFIG_DIR, CONFIG_FILENAME)
if not pathlib.Path.exists(CONFIG_FILE_PATH):
    error = f"Couldn't find {CONFIG_FILENAME} please add to {CONFIG_DIR}"
    logger.error(error)
    raise FileNotFoundError(error)


with CONFIG_FILE_PATH.open() as f:
    CONFIG = yaml.safe_load(f)


DATE_FORMAT = "%Y-%m-%d"
