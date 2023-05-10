from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

from config import CONFIG, get_logger

logger = get_logger(__name__)


def open_ssh_tunnel(server_name: str):
    with SSHTunnelForwarder(
        (CONFIG[server_name]["host"], 22),  # Remote server IP and SSH port
        ssh_username=CONFIG[server_name]["os_user"],
        remote_bind_address=("127.0.0.1", 5432),
    ) as server:  # PostgreSQL server IP and sever port on remote machine
        logger.info(f"Start SSH tunnel to {server_name=}")
        # server.start()  # start ssh sever
        logger.info(f"Opened SSH Tunnel {server_name=}")
    return server


def get_db_connection(server_name: str):
    """Returns a PostgresCon class
    to use class run server.set_engine()
    ====
    Parameters
       server_name: str String of server name for parsing config file
    """
    server_ip, server_local_port = get_postgres_server_ips(server_name)
    postgres_con = PostgresCon(server_name, server_ip, server_local_port)
    return postgres_con


def get_postgres_server_ips(server_name: str) -> tuple[str, str]:
    db_ip = CONFIG[server_name]["host"]
    if db_ip == "localhost" or db_ip.startswith("172"):
        db_ip = CONFIG[server_name]["host"]
        db_port = str(5432)
    else:
        logger.info(f"Opening SSH tunnel to {server_name=}")
        ssh_server = open_ssh_tunnel(server_name)
        ssh_server.start()
        db_port = str(ssh_server.local_bind_port)
        db_ip = "127.0.0.1"
    logger.info(f"Connecting {db_ip=} {db_port=}")
    return db_ip, db_port


class PostgresCon:
    """Class for managing the connection to postgres
    Parameters:
    ----------------
        my_db: String, passed on init, string name of db
        my_env: String, passed on init, string name of env, 'staging' or 'prod'
    """

    engine = None
    db_name = None
    db_pass = None
    db_uri = None
    db_user = None

    def __init__(self, my_db, db_ip=None, db_port=None):
        self.db_name = my_db
        self.db_ip = db_ip
        self.db_port = db_port
        try:
            self.db_user = CONFIG[self.db_name]["user"]
            self.db_pass = CONFIG[self.db_name]["password"]
            logger.info("Auth data loaded")
        except Exception as error:
            logger.exception(f"Loading db_auth for {self.db_name}, error: {error}")

    def set_engine(self):
        try:
            self.db_uri = f"postgresql://{self.db_user}:{self.db_pass}"
            self.db_uri += f"@{self.db_ip}:{self.db_port}/{self.db_name}"
            self.engine = create_engine(
                self.db_uri,
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "ads-crawler-dash",
                },
            )
            logger.info(f"Created PostgreSQL Engine {self.db_name}")
        except Exception as error:
            logger.exception(
                f"PostgresCon failed to connect to {self.db_name}@{self.db_ip} {error=}"
            )
            self.db_name = None
