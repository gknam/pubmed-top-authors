import os
import re

import urllib, json

from flask import Flask, jsonify, render_template, request, url_for
from flask_jsglue import JSGlue

from helpers import getPmids, getFullRecs, topAuthorsRecs


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
#db = SQL("sqlite:///mashup.db")

@app.route("/")
def index():
    """Render map."""
    return render_template("index.html")

@app.route("/records")
def records():
    """Retreive key records of authors with most publications."""
    
    # ensure parameter is present
    if not request.args.get("term"):
        raise RuntimeError("missing term")

    # get pmids for term
    term = request.args.get('term')
    retmax = request.args.get('retmax')
    reldate = request.args.get('reldate')
    numTopAuthors = int(request.args.get('numTopAuthors'))
    searchOption = request.args.get('searchOption')
    
    try:
        pmids = getPmids(term, retmax, reldate, searchOption)
    except:
        return jsonify("error")
    
    # get full records from pmids
    if pmids:
        records, pmidsAll_len, pmidsInc_len, pubYear_oldest = getFullRecs(pmids)
    else:
        return jsonify({})
    
    # get summary from full records
    topRecs = topAuthorsRecs(records, pmidsAll_len, pmidsInc_len, pubYear_oldest, numTopAuthors)
    return jsonify(topRecs)
