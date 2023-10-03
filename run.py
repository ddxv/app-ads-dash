from functools import wraps

from flask import Response, redirect, render_template, request, url_for

from config import get_logger
from dashapp import app as dashapp
from dbcon.queries import (
    get_apps_by_name,
    get_appstore_categories,
    get_dash_users,
    get_single_app,
    get_top_apps_by_installs,
)
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


@server.route("/dash")
@requires_auth
def appads():
    logger.info("Loading dash")
    return render_template("dashboard.html", template="Flask")


@server.route("/")
@requires_auth
def home():
    logger.info("Loading home page")
    return redirect(url_for("/dash/"))


@server.route("/apps")
def apps_home():
    logger.info("Loading app dash")
    cats = get_appstore_categories()
    category_dicts = cats.to_dict(orient="records")
    return render_template("apps_home.html", cats=category_dicts)


@server.route("/<store>/<app_id>")
def app_detail(store, app_id):
    # Fetch app details from the database using store and app_id
    app = get_single_app(app_id)
    app_dict = app.to_dict(orient="records")[0]
    print(app_dict)
    return render_template("app_detail.html", app=app_dict)


@server.route("/category/<category>")
def category(category):
    # Your logic here for handling the category page
    apps = get_top_apps_by_installs(category_in=[category], limit=15)
    apps_dict = apps.to_dict(orient="records")
    return render_template("category_detail.html", category=category, apps=apps_dict)


@server.route("/search")
def search():
    query = request.args.get("query")
    apps = get_apps_by_name(query)
    apps_dict = apps.to_dict(orient="records")
    return render_template("search_results.html", apps=apps_dict, query=query)


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")
