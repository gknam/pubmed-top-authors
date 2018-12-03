# pubmed-top-authors

Visit [Pubmed's top authors](https://pubmed-top-authors-gknam.c9users.io/) website.

<a href="https://www.youtube.com/watch?v=jXctQUTaPcY" target="_blank"><img src="pubmed_top_authors.png" alt="pubmed_authors" style="float:left" /></a>

This is a data visualisation website. When the user types in a keyword (e.g. psychology) or an author's name, the website identifies top authors (i.e. authors who published most) on Pubmed  (1) on a keyword or (2) together with a specified author. Then, each author's publication counts are visualised in interactive plots (1) per year and (2) per journal.

# 1. Usage
## Setup
1. Make an account at [Cloud9](https://c9.io), and [create a workspace](https://docs.c9.io/v1.0/docs/create-a-workspace) choosing **Python** as a template.

2. Open a terminal (if there is none already open).

*Now, copy the command in each of the following steps and paste it into the terminal.*
<br>

2. download repository.

   `git clone https://github.com/gknam/pubmed-top-authors.git`

3. Go into the repository.

   `cd pubmed-top-authors`

4. Change the default python version to 3.4

   `sudo ln -sfn python3.4 /usr/bin/python`

5. Install required packages

   `sudo pip install -r requirements.txt`

6. Setup Flask.

   `export FLASK_APP=application.py`

   `export FLASK_DEBUG=1`

## Start server

There are two versions of this website.

#### Version 1 (recommended)

1. Go to the branch for this version.

   `git checkout original_only`

2. Initiate server.

   `flask run --host=0.0.0.0 --port=8080`

3. Open website

   In the terminal, *left*-click on `http://0.0.0.0:8080/` and select **Open**.

#### Version 2

1. Go to the branch for this version.

   `git checkout master`

2. Initiate server.

   `flask run --no-reload --host=0.0.0.0 --port=8080`

3. Open website

   In the terminal, *left*-click on `http://0.0.0.0:8080/` and select **Open**.

4. Select **Database to query**

   **Original**: Fetch data directly from Pubmed (same as **Version 1**).

   **Extracts from original**: Fetch data from a local database file*, which contains data pre-fetched from Pubmed.

*The local database file is initially empty, and complete update is assumed to take a few **months**.*

## Kill server

To kill the server, do the following with the the **terminal in which** `flask` **command is running**.

* Click anywhere in the terminal and press `Ctrl` + `C`.
* Close the terminal

If you want to restart the server, follow the instructions in **Start server** section above.

*You might want to kill the server and restart it in case you want to stop a search and do a new one. Search will be slower with bigger numbers typed in "Max number of days from today and/or "Max number of articles to check" on the website.*

# 2. Technical notes

## Languages, packages and framework used
* Backend
   * Python
       * [Flask](http://flask.pocoo.org/)
   * SQLite3 (via Python's [SQLAlchemy](https://www.sqlalchemy.org/))
   * [xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html)
* Frontend
   * HTML
   * CSS
   * JavaScript
       * [D3.js](https://d3js.org/)
       * [jQuery](https://jquery.com/)
       * [jQueryUI](https://jqueryui.com/)
       * [Bootstrap](https://getbootstrap.com/)
       * [typeahead.js](https://twitter.github.io/typeahead.js/)
       * [Handlebars.js](https://handlebarsjs.com)

## Procedure

### 1. User submits query (front-end)

The user types in a keyword (e.g. psychology) or an author's name in the search bar. The user can also specify the (1) data fetching method - which will be explained below - , (2) number of top authors to identify, (3) date range going backwards from today, and (4) maximum number of articles (i.e. publications) to check. The set of parameters is sent to the back-end in JSON format.

jQuery is used to use simplified syntax.

### 2. Fetch data (back-end)

In the back-end, data is fetched according to the parameters. The data to fetch includes various details of each publication (e.g. author name, publication year, journal title, etc.).

The data can be fetched from either of two sources.

### 2.1. Pubmed's database

Data are fetched using [Pubmed API](https://www.ncbi.nlm.nih.gov/books/NBK25501/).

Pro: Fetched data is reliable because this accesses the original database
Cons: Retrieving data via Pubmed API can be slow especially when the query range (date range, maximum number of articles) is big. Also, Pubmed API sets a rather tight limit on query range.

### 2.2. SQLite database file (DB) stored in this website's server

The DB contains data pre-fetched from Pubmed.

Pro: Depending on the computing resources, (1) the allowed query range can be bigger than that set by Pubmed API and (2) the retrieval speed can be quicker.
Cons: Fetched data is less reliable because DB can never be 100% up-to-date with Pubmed's database - auto-update function runs every 10 minutes.

### 2.2.1. Pre-fetch data

Data pre-fetching is run in the background. The following download-ETL cycle continues until all update is finished.

If the server is killed and resumed, update will resume from the last-fetched XML file. Once all data is pre-fetched, updates are checked for every 10 minutes.

### 2.2.1.1. Download

XML files are downloaded from Pubmed's FTP server - [baseline data](ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline) are downloaded and saved first before [update data](ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/)).

### 2.2.1.2. ETL (Extract, Transform, Load)

From XML file, relevant elements (i.e. information) are extracted using [xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html), then transformed into Python data type (e.g. [set](https://docs.python.org/2/library/sets.html)), and loaded into the DB using SQLite and [SQLAlchemy](https://www.sqlalchemy.org/). 

### 3. Identify top authors (back-end)

Within the fetched data, top authors are identified who have most publications (1) on the specified keyword or (2) together with the specified author. Then, the top authors' data are sent to the front-end in JSON format.

### 4. Reorganise and visualise top authors' data (front-end)

Data are reorganised. Then, using [D3.js](https://d3js.org/), each author's publication counts are visualised in interactive plots (1) per year and (2) per journal.

\*PostgreSQL would be a more appropriate choice than SQLite. This is because SQLite DB gets locked for a few milliseconds each time it gets updated, and DB is inaccessible during this. This is likely to be disruptive because the DB update constantly runs in the background.