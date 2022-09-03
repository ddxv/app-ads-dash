from config import CONFIG, get_logger
import os
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

logger = get_logger(__name__)


def OpenSSHTunnel(server_name):
    with SSHTunnelForwarder(
        (CONFIG[server_name]["host"], 22),  # Remote server IP and SSH port
        ssh_username=CONFIG[server_name]["os_user"],
        # ssh_pkey=CONFIG["ssh"]["pkey"],
        # ssh_private_key_password=CONFIG["ssh"]["pkey_password"],
        remote_bind_address=("127.0.0.1", 5432),
    ) as server:  # PostgreSQL server IP and sever port on remote machine
        server.start()  # start ssh sever
        logger.info(f"Connecting via SSH {server_name=} and bind to local")
    return server


def get_db_connection(server_name: str):
    """Returns a PostgresCon class
    to use class run server.set_engine()
    ====
    Parameters
       server_name: str String of either hydra or netx
    """
    server_ip, server_local_port = get_postgres_server_ips(server_name)
    postgres_con = PostgresCon(server_name, server_ip, server_local_port)
    return postgres_con


def get_postgres_server_ips(server_name: str) -> tuple[str, str]:
    # PROD, set in the OS environment, is true if python running in EC2 security group
    if "PROD" in os.environ and os.environ["PROD"] == "True":
        logger.info("Prod environment mode no SSH")
        server_ip = CONFIG[server_name]["host"]
        server_local_port = 5432
    else:
        logger.info("Connecting via SSH tunnel")
        ssh_server = OpenSSHTunnel(server_name)
        ssh_server.start()
        server_local_port = str(ssh_server.local_bind_port)
        server_ip = "127.0.0.1"
    return server_ip, server_local_port


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