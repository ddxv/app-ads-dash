import pathlib
import yaml
import logging

HOME = pathlib.Path.home()
TOP_CONFIGDIR = pathlib.Path(HOME, pathlib.Path(".config"))
CONFIG_DIR = pathlib.Path(TOP_CONFIGDIR, pathlib.Path("app-ads"))
LOG_DIR = pathlib.Path(CONFIG_DIR, pathlib.Path("logs"))
MODULE_DIR = pathlib.Path(__file__).resolve().parent.parent


def check_config_dirs():
    dirs = [TOP_CONFIGDIR, CONFIG_DIR, LOG_DIR]
    for dir in dirs:
        if not pathlib.Path.exists(dir):
            pathlib.Path.mkdir(dir, exist_ok=True)


def get_logger(mod_name):
    format = "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
    logger = logging.getLogger(mod_name)
    check_config_dirs()
    filename = f"{LOG_DIR}/dash.log"
    # Writes to file
    logging.basicConfig(format=format, level=logging.INFO, filename=filename)
    # Writes to stdout
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(format))
    logger.addHandler(ch)
    return logger


logger = get_logger(__name__)


CONFIG_FILENAME = "config.yml"

CONFIG_FILE_PATH = pathlib.Path(CONFIG_DIR, CONFIG_FILENAME)
if not pathlib.Path.exists(CONFIG_FILE_PATH):
    error = f"Couldn't find {CONFIG_FILENAME} please add to {CONFIG_DIR}"
    logger.error(error)
    raise FileNotFoundError(error)


with CONFIG_FILE_PATH.open() as f:
    CONFIG = yaml.safe_load(f)


DATE_FORMAT = "%Y-%m-%d"


