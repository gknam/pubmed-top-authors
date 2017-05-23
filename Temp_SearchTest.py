import os
import re
import urllib, json

from flask import Flask, jsonify, render_template, request, url_for
from flask_jsglue import JSGlue

from helpers import getUids, getFullRecs, topFive


def search():
    """Search for places that match query."""

#    # ensure parameter is present
#    if not request.args.get("q"):
#        raise RuntimeError("missing query")
#
#    # fetch places that begins with query
    q = "preterm"

    # get UIDs from Pubmed (for the last 5 years's records)

    url = "https://www.ncbi.nlm.nih.gov/portal/utils/autocomp.fcgi?dict=pm_related_queries_2&q={}".format(urllib.parse.quote(q))
    feed = urllib.request.urlopen(url)
    data = feed.read().decode("utf-8")
    
    data = re.split('\(|\)', data)[2]
    data = re.split(('",\ "|"'), data)[1:-1]
    print(data)

    return data

search()