from typing import Self

from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

from config import CONFIG, get_logger

logger = get_logger(__name__)


class PostgresCon:
    """Class for managing the connection to postgres.

    Parameters
    ----------
        my_db: String, passed on init, string name of db
        my_env: String, passed on init, string name of env, 'staging' or 'prod'

    """

    engine = None
    db_name = None
    db_pass = None
    db_uri = None
    db_user = None

    def __init__(
        self: Self,
        my_db: str,
        db_ip: str | None = None,
        db_port: str | None = None,
    ) -> None:
        """Initialize connection with ports and dbname."""
        self.db_name = my_db
        self.db_ip = db_ip
        self.db_port = db_port
        try:
            self.db_user = CONFIG[self.db_name]["db_user"]
            self.db_pass = CONFIG[self.db_name]["db_password"]
            logger.info("Auth data loaded")
        except Exception as error:
            msg = f"Loading db_auth for {self.db_name}, error: {error}"
            logger.exception(msg)

    def set_engine(self: Self) -> None:
        """Set postgresql engine."""
        try:
            self.db_uri = f"postgresql://{self.db_user}:{self.db_pass}"
            self.db_uri += f"@{self.db_ip}:{self.db_port}/{self.db_name}"
            self.engine = create_engine(
                self.db_uri,
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "app-store-dash",
                },
            )
            logger.info(f"Created PostgreSQL Engine {self.db_name}")
        except Exception as error:
            msg = (
                f"PostgresCon failed to connect to {self.db_name}@{self.db_ip} {error=}"
            )
            logger.exception(msg)
            self.db_name = None


def open_ssh_tunnel(server_name: str) -> SSHTunnelForwarder:
    """Create SSH tunnel when working remotely."""

    ssh_port = CONFIG[server_name].get("ssh_port", 22)
    ssh_host = CONFIG[server_name]["host"]
    ssh_username = CONFIG[server_name]["os_user"]
    ssh_pkey = CONFIG[server_name].get("ssh_pkey", None)
    ssh_private_key_password = CONFIG[server_name].get("ssh_pkey_password", None)
    with SSHTunnelForwarder(
        (ssh_host, ssh_port),  # Remote server IP and SSH port
        ssh_username=ssh_username,
        ssh_pkey=ssh_pkey,
        ssh_private_key_password=ssh_private_key_password,
        remote_bind_address=("127.0.0.1", 5432),
    ) as server:  # PostgreSQL server IP and sever port on remote machine
        logger.info(f"Start SSH tunnel to {server_name=}")
        logger.info(f"Opened SSH Tunnel {server_name=}")
    return server


def get_db_connection(server_name: str) -> PostgresCon:
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
    if db_ip == "localhost" or db_ip.startswith("192"):
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
