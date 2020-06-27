import os
import dataset
import datetime
import time

from bottle import Bottle, route, run, template, request, static_file, response
from utils import ellapsed_time
from json import dumps

app = Bottle()

PROJECT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_URI = 'postgresql://primicia:primiciapassword!@0.0.0.0:5432/primicia'
DB_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URI)
db = dataset.connect(DB_URI)

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
    query = """
    SELECT *
    FROM news
    ORDER BY "dateAdded" DESC, visits DESC, "datetimeAdded" DESC
    OFFSET {}
    LIMIT {}
    """.format(offset, limit)
    news = db.query(query)

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


# static files
@route('/static/<filename:path>')
def static_files(filename):
    """Serve static files"""
    return static_file(filename, root='{0}/static/'.format(PROJECT_PATH))

if os.environ.get('APP_LOCATION') == 'dokku':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    run(host='localhost', port=8080, debug=True)