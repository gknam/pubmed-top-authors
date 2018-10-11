# pubmed-top-authors

<a href="https://www.youtube.com/watch?v=jXctQUTaPcY" target="_blank"><img src="pubmed_top_authors.png" alt="pubmed_authors" style="float:left" /></a>

Find authors on [**Pubmed**](https://www.ncbi.nlm.nih.gov/pubmed/) who published most (1) on a keyword or (2) together with an author.
Then draw graphs on their publication records per year and per journal.

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
## Data fetching

### Version 1
All data are fetched directly from Pubmed via [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/).

### Version 2

Using the **Database to query** selector, Data can be fetched (1) the same way as Version 1 or (2) from a database file (DBF) stored in this website's server. The DBF (**database/pubmed.db**) contains data pre-fetched from Pubmed via [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/).

**Data pre-fetching**: When the server starts (i.e. `flask` is run), data in XML format start getting fetched from Pubmed's FTP server ([baseline](http://bit.ly/2hMJru1) and [updatefiles](http://bit.ly/2y0kwcr)) and transferred into the DBF in the background. This continues until all update is finished. If the server is killed and resumed, update will resume from the last-fetched XML file.
