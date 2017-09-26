from sqlalchemy import create_engine

from flask import Flask, jsonify, render_template, request
from flask_jsglue import JSGlue
from helpers import dbConExe, getPmids, getFullRecs_ori, getFullRecs_ext, \
                    topAuthorsRecs, call_in_background, updateDbStart

# configure application
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False # prevent jsonify from reordering dictionary (http://bit.ly/2qWaxhx)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure CS50 Library to use SQLite database
db_file = "database/pubmed.db"
db = create_engine("sqlite:///" + db_file)

# create db if it does not exist
with open(db_file, "a") as f:
    pass

# create "medline" table if it does not exist
# pmid: pmid (unique identifier of each pubmed article)
# crYmd, coYmd, reYmd: date MEDLINE record was created, completed and
# revised dates (format: yyyymmdd). Order of recency is crYmd < coYmd < reYmd
# fiYmd: most recent date available among crYmd, coYmd and reYmd.
# fname: first name
# lname: last name
# initials: initials of first name
# pyear, pmonth, pday: publication year, month and day
# journal: journal title (abbreviated)
# journalNonAbbr: journal title (non-abbreviated)
# article: article title
# doi: digital object identifier
# journalVol: journal volume
# journalIss: journal issue
# pageNum: page numbers
# country: country where journal was published


dbConExe(db, "CREATE TABLE IF NOT EXISTS medline \
            (pmid INTEGER NOT NULL PRIMARY KEY, \
            fiYmd TEXT NOT NULL, crYmd TEXT NOT NULL, coYmd TEXT, reYmd TEXT, \
            fname TEXT NOT NULL, lname TEXT NOT NULL, initials TEXT, \
            pyear TEXT NOT NULL, pmonth TEXT, pday TEXT, \
            journal TEXT NOT NULL, journalNonAbbr TEXT, article TEXT, doi TEXT, \
            journalVol TEXT, journalIss TEXT, pageNum TEXT, country TEXT)")


threaded_ticker = call_in_background(updateDbStart, db)

@app.route("/")
def index():
    """Load homepage"""
    return render_template("index.html")

@app.route("/records")
def records():
    """Retreive key records of authors with most publications."""
    global db

    # ensure parameter is present
    if not request.args.get("term"):
        raise RuntimeError("missing term")

    # get pmids for term
    term = request.args.get('term')
    retmax = request.args.get('retmax')
    reldate = request.args.get('reldate')
    numTopAuthors = int(request.args.get('numTopAuthors'))
    searchOption = request.args.get('searchOption')
    databaseOption = request.args.get('databaseOption')

    try:
        pmids = getPmids(term, retmax, reldate, searchOption)
    except:
        return jsonify("error")

    # get full records from pmids
    if pmids:
        if databaseOption == "extract":
            records, pmidsAll_len, pmidsInc_len, pubYear_oldest = getFullRecs_ext(db, pmids)
        elif databaseOption == "original":
            records, pmidsAll_len, pmidsInc_len, pubYear_oldest = getFullRecs_ori(pmids)
    else:
        return jsonify({})

    # get summary from full records
    topRecs = topAuthorsRecs(records, pmidsAll_len, pmidsInc_len, pubYear_oldest, numTopAuthors)
    return jsonify(topRecs)