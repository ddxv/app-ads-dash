from functools import wraps

from flask import Response, redirect, render_template, request, url_for

from config import get_logger
from dashapp import app as dashapp
from dbcon.queries import (
    get_app_history,
    get_apps_by_name,
    get_appstore_categories,
    get_dash_users,
    get_single_app,
    get_top_apps_by_installs,
    query_recent_apps,
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


@server.route("/apps/")
def apps_home():
    logger.info("Loading apps home")
    recent_apps = query_recent_apps(days=7)
    trending_apps = query_recent_apps(days=30)
    trending_ios_apps = trending_apps[~trending_apps["store"].str.contains("oogl")]
    trending_google_apps = trending_apps[trending_apps["store"].str.contains("oogl")]
    recent_google_apps = recent_apps[recent_apps["store"].str.contains("oogl")]
    recent_ios_apps = recent_apps[~recent_apps["store"].str.contains("oogl")]
    cats = get_appstore_categories()
    # Make app count strings
    cats["android"] = cats["android"].apply(
        lambda x: "{:,.0f}".format(x) if x else "N/A"
    )
    cats["ios"] = cats["ios"].apply(lambda x: "{:,.0f}".format(x) if x else "N/A")
    category_dicts = cats.to_dict(orient="records")
    recent_ios_dicts = recent_ios_apps.to_dict(orient="records")
    recent_google_dicts = recent_google_apps.to_dict(orient="records")
    trending_google_dicts = trending_google_apps.to_dict(orient="records")
    trending_ios_dicts = trending_ios_apps.to_dict(orient="records")
    trending_title = "Trending Apps this Month"
    recent_title = "New Apps this Month"
    trending_dicts = {}
    trending_dicts[trending_title] = {}
    trending_dicts[recent_title] = {}
    trending_dicts[trending_title]["Google Play"] = trending_google_dicts
    trending_dicts[trending_title]["iOS"] = trending_ios_dicts
    trending_dicts[recent_title]["Google Play"] = recent_google_dicts
    trending_dicts[recent_title]["iOS"] = recent_ios_dicts
    return render_template(
        "apps_home.html",
        cats=category_dicts,
        trending_apps=trending_dicts,
    )


@server.route("/")
def home():
    logger.info("Loading home page")
    return redirect(url_for("apps_home"))


@server.route("/apps/<app_id>")
def app_detail(app_id):
    # Fetch app details from the database using store and app_id
    logger.info(f"/apps/{app_id=} start")
    app = get_single_app(app_id)
    app_dict = app.to_dict(orient="records")[0]
    app_hist = get_app_history(store_app=app_dict["id"])
    app_dict["history"] = app_hist.to_html()
    logger.info(f"/apps/{app_id=} return render_template")
    return render_template("app_detail.html", app=app_dict)


@server.route("/category/<category>")
def category(category):
    # Your logic here for handling the category page
    apps = get_top_apps_by_installs(category_in=[category], limit=15)
    apps_dict = apps.to_dict(orient="records")
    return render_template("category_detail.html", category=category, apps=apps_dict)


@server.route("/search/")
def search():
    query = request.args.get("query")
    if not query:
        return render_template("search_no_query.html")
    apps = get_apps_by_name(query)
    apps_dict = apps.to_dict(orient="records")
    return render_template("search_results.html", apps=apps_dict, query=query)


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")
