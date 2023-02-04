from config import get_logger

logger = get_logger(__name__)
logger.info("Load IDs")

# Home Page
HOME_TAB = "home-about"

# Analytics Tab IDs
NETWORKS = "networks"
NETWORK_UNIQUES = "network-uniques"
DEVELOPERS_SEARCH = "developers-search"
TXT_VIEW = "txt-view"

# Internal Tab IDs
INTERNAL_LOGS = "internal-logs"
STORE_APPS_HISTORY = "internal-overview"
PUB_URLS_HISTORY = "pub-urls"

# Tab Options
AFFIX_DATE_PICKER = "-date-picker"
AFFIX_RADIOS = "-radios"
AFFIX_PLOT = "-plot"
AFFIX_GROUPBY = "-groupby"
AFFIX_GROUPBY_TIME = "-groupby-time"
AFFIX_SWITCHES = "-switches"
AFFIX_TABLE = "-table"
AFFIX_BUTTON = "-button"
AFFIX_SEARCH = "-search"
AFFIX_LOADING = "-loading"

# Combined Components Names
TXT_VIEW_TABLE = TXT_VIEW + AFFIX_TABLE
