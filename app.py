import os
import dataset
import datetime
import logging

from bottle import Bottle, route, run, template, request, static_file, response, TEMPLATES
from utils import ellapsed_time
from json import dumps

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

TEMPLATES.clear()

app = Bottle()

PROJECT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_URI = 'postgresql://primicia:primiciapassword!@0.0.0.0:5432/primicia'
DB_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URI)
db = dataset.connect(DB_URI)

ALLOWED_SITES = {
    "zetatijuana.com",
    "elvigia.net",
    "ensenada.net",
    "el-mexicano.com",
    "radanoticias.info",
    "elimparcial.com",
}


# the decorator
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors


@route("/")
@route("/news")
def news():
    page = request.GET.get("p", 1)
    try:
        page = int(page)
    except:
        page = 1
    limit = 30
    offset_page = page - 1
    offset = offset_page * limit
    start = 1 + (offset_page * limit)
    # For ordering, the more time has elapsed, the less weight the news is going to have
    query = """
    SELECT *,
    (1+visits)/power((extract(EPOCH from age(now(), "datetimeAdded"))/3600)+2, 1.8) as order_weight
    FROM news
    ORDER BY order_weight DESC
    OFFSET {}
    LIMIT {}
    """.format(offset, limit)
    news_result = db.query(query)
    news = []
    ids = []
    for new in news_result:
        ids.append(str(new['id']))
        news.append(new)

    logging.debug(", ".join(ids))
    # for new in news:
    #     ellapsed = time.time() - new["datetimeAdded"].timestamp()
    #     print(hms(ellapsed))

    return template("news", news=news, page=page, start=start,ellapsed_time=ellapsed_time)

@route("/news/<id:int>/visits", method="POST")
def visits(id):
    table = db["news"]
    new_entry = table.find_one(id=id)
    new_visits = new_entry['visits'] + 1

    table.update(dict(id=id, visits=new_visits), ['id'])

    response.content_type = 'application/json'
    return dumps({"message": "success"})


# API routes
@route("/api/news")
@enable_cors
def api_news():
    page = request.GET.get("page", 1)
    order = request.GET.get("order", "relevant")
    date = request.GET.get("date", None)
    sites = request.query.getall('sites') or []

    try:
        page = int(page)
    except:
        page = 1
    limit = 30
    offset_page = page - 1
    offset = offset_page * limit
    start = 1 + (offset_page * limit)

    filters = []
    order_field = "visits, \"datetimeAdded\"" if order == "relevant" else "\"datetimeAdded\""

    dt_obj = datetime.datetime.strptime(date, '%Y%m%d') if date else datetime.datetime()
    date_value = dt_obj.strftime("%Y-%m-%d")
    filters.append(f"\"dateAdded\" = '{date_value}'")
    
    if sites:
        valid_sites = set(sites).intersection(ALLOWED_SITES)
        if len(valid_sites) > 0:
            sites_value = ",".join([f"'{site}'" for site in valid_sites])
            filters.append(f"website IN ({sites_value})")

    filters_query = "WHERE " + " AND ".join(filters) if filters else ""

    # For ordering, the more time has elapsed, the less weight the news is going to have
    query = """
    SELECT *
    FROM news
    {}
    ORDER BY {} DESC
    OFFSET {}
    LIMIT {}
    """.format(filters_query, order_field, offset, limit)

    news_result = db.query(query)

    news = []
    ids = []
    for new in news_result:
        new["ellapsed_time"] = ellapsed_time(new["datetimeAdded"])
        del new["datetimeAdded"]
        news.append(new)

    response.content_type = 'application/json'
    return dumps({"data": news})


# static files
@route('/static/<filename:path>')
def static_files(filename):
    """Serve static files"""
    return static_file(filename, root='{0}/static/'.format(PROJECT_PATH))


if os.environ.get('APP_LOCATION') == 'dokku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    run(host='localhost', port=8080, debug=True)
