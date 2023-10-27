from functools import wraps

from flask import Response, request

from config import get_logger
from dashapp import app as dashapp
from dbcon.queries import get_dash_users
from server import server

logger = get_logger(__name__)


logger.info(f"start, {dashapp=}")

DASH_USERS_DICT = get_dash_users()


def check_auth(username, password):
    try:
        if password == DASH_USERS_DICT[username]["password"]:
            login = True
        else:
            login = False
        logger.info(f"Check Login {username=} {login=}")
    except Exception:
        login = False
    return login


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@server.route("/")
def home():
    logger.info("Loading home page")


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")
