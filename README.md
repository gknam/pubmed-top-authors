> [!IMPORTANT]
> Branches have been changed as shown below on 2023-11-05 (Sunday).
> 
> * `original_only` -> **`main`**
> * **`master`** -> `both_versions`
> 
> The two branches differ as described below.
> 
> * In **`main`** branch, data is fetched directly from the Pubmed API.
> * In **`both_versions`** branch, data can be fetched either [directly from the Pubmed API](#91-original-recommended) or [from a local database which contains copies of those data](#92-extracts-from-original).

> [!NOTE]
> This branch is currently **NOT WORKING** because [start server](#7-start-server) step fails.

# Pubmed's top authors

<a href="https://www.youtube.com/watch?v=jXctQUTaPcY" target="_blank"><img src="pubmed_top_authors.png" alt="pubmed_authors" style="float:left" /></a>

This is a data visualisation website. When the user types in a keyword (e.g. psychology) or an author's name, the website identifies top authors (i.e. authors who published most) on Pubmed  (1) on a keyword or (2) together with a specified author. Then, each author's publication counts are visualised in interactive plots (1) per year and (2) per journal.

# 1. Usage
## Setup
### 1. Make an account at [Cloud9](https://c9.io), and [create a workspace](https://docs.c9.io/v1.0/docs/create-a-workspace) choosing **Python** as a template.

### 2. Open a terminal (if there is none already open).

*Now, copy the command in each of the following steps and paste it into the terminal.*
<br>

### 3. download repository.

   ```
   git clone https://github.com/gknam/pubmed-top-authors.git
   ```

### 4. Go into the repository.

   ```
   cd pubmed-top-authors
   ```

### 5. Install required packages
   
   ```
   sudo pip3 install -r requirements.txt
   ```

### 6. Setup Flask
   
   ```
   export FLASK_APP=application.py
   ```
   
   ```
   export FLASK_DEBUG=1
   ```

### 7. Start server

   ```
   flask run --no-reload --host=0.0.0.0 --port=8080
   ```

### 8. Open website

   Go to `Preview` --> `Preview Running Application`

### 9. Select **Database to query**
There are two options:

   #### 9.1. **Original** (recommended)
   * This mode is **more reliable** although slower.
   * Data is fetched directly from Pubmed (as explained [here](#21-pubmeds-database)).
   #### 9.2. **Extracts from original**
   * This mode is faster, but unreliable because it was not fully tested.
   * Data is fetched from a local database file, which contains data pre-fetched from Pubmed (as explained [here](#22-database-in-this-websites-server)).
     * The local database is initially empty.
     * When the server starts, the local database should start being updated by downloading data chunk by chunk from Pubmed API.
     * Complete update of the local database is assumed to take a few **months**.

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

The user types in a keyword (e.g. psychology) or an author's name in the search bar. The user can also specify the (1) data fetching method - which will be explained below - , (2) number of top authors to identify, (3) date range going backwards from today, and (4) maximum number of articles (i.e. publications) to check. The set of search criteria are sent to the back-end in JSON format.

jQuery is used for simplified syntax.

### 2. Identify publications (back-end)

In the back-end, publications that match the search criteria are identified.

### 2. Fetch data (back-end)

Data are fetched for each identified publication. The fetched data include various details of each publication (e.g. author name, publication year, journal title, etc.).

The data can be fetched from either of two sources: **Pubmed's database** or the **database in this website's server**.

### 2.1. Pubmed's database

Data are downloaded from Pubmed's database via [Pubmed API](https://www.ncbi.nlm.nih.gov/books/NBK25501/) as XML files. From the XML files, relevant elements (i.e. information) are **E**xtracted using [xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html), then **T**ransformed into a Python [dictionary](https://docs.python.org/3.7/tutorial/datastructures.html?highlight=dictionary#dictionaries). 

*Pro: Fetched data are reliable because this accesses the original database*

*Cons: Retrieving data via Pubmed API can be slow especially when the query range (date range, maximum number of articles) is big. Also, Pubmed API sets a rather tight limit on query range.*

### 2.2. Database in this website's server

Data are fetched from the SQLite* database file (DB) in the server. The fetched data are transformed into a Python dictionary.

The DB contains data which have been "pre"-fetched from Pubmed. This procedure is explained in the following subsections **2.2.1** to **2.2.1.2**.

*Pro: Depending on the computing resources, (1) the allowed query range can be bigger than that set by Pubmed API and (2) the retrieval speed can be quicker.*

*Cons: Fetched data are less reliable because DB can never be 100% up-to-date with Pubmed's database - auto-update function runs every 10 minutes.*

> [!NOTE]
> \*PostgreSQL would be a more appropriate choice than SQLite. This is because SQLite DB gets locked for a few milliseconds each time it gets updated, and DB is inaccessible during this. This is likely to be disruptive because the DB update constantly runs in the background.


### 2.2.1. Pre-fetch data

Data pre-fetching is run in the background. The following download-[**ETL**](https://en.wikipedia.org/wiki/Extract,_transform,_load) cycle continues until all update is finished.

If the server is killed and resumed, update will resume from the last-fetched XML file. Once all data are pre-fetched, updates are checked for every 10 minutes.

### 2.2.1.1. Download

XML files are downloaded from Pubmed's FTP server - [baseline data](ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline) are downloaded and saved first before [update data](ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/)).

### 2.2.1.2. [ETL (Extract, Transform, Load)](https://en.wikipedia.org/wiki/Extract,_transform,_load)

From XML file, relevant elements (i.e. information) are **E**xtracted using [xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html), then **T**ransformed into a Python [set](https://docs.python.org/2/library/sets.html), and **L**oaded into the DB using SQLite and [SQLAlchemy](https://www.sqlalchemy.org/). 

### 3. Identify top authors (back-end)

Within the fetched data, top authors are identified who have most publications (1) on the specified keyword or (2) together with the specified author. Then, the top authors' data are sent to the front-end in JSON format.

### 4. Reorganise and visualise top authors' data (front-end)

Data are reorganised. Then, using [D3.js](https://d3js.org/), each author's publication counts are visualised in interactive plots (1) per year and (2) per journal.
