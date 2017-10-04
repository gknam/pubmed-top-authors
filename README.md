# pubmed-top-authors
Find authors on Pubmed who published most (1) on a keyword or (2) together with an author.
Then draw graphs on their publication records per year and per journal.

# Setup
1. Make an account at [Cloud9](https://c9.io), and [create a workspace](https://docs.c9.io/v1.0/docs/create-a-workspace) choosing **Python** as a template.

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

# Execute

There are two versions of this website.

### Version 1 (recommended)
*All data are fetched directly from Pubmed via [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/).*

1. Go to the branch for this version.

   `git checkout original_only`

2. Initiate server.

   `flask run --host=0.0.0.0 --port=8080`

3. Open website

   In the terminal, *left*-click on `http://0.0.0.0:8080/` and select **Open**.

### Version 2
*Data can be fetched (1) the same way as Version 1 or (2) from a database file (DBF) stored in this website's server. The DBF (**database/pubmed.db**) contains data pre-fetched from Pubmed via [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/).*

**Data pre-fetching**: When the server starts (i.e. `flask` is run), data in XML format start getting fetched from Pubmed's FTP server ([baseline](http://bit.ly/2hMJru1) and [updatefiles](http://bit.ly/2y0kwcr)) and transferred into the DBF in the background. This continues until all update is finished. If the server is killed and resumed, update will resume from the last-fetched XML file.

**Warning**: The DBF is initially empty, and complete update of the DBF is assumed to take a few *months*.

1. Go to the branch for this version.

   `git checkout master`

2. Initiate server.

   `flask run --no-reload --host=0.0.0.0 --port=8080`

3. Open website

   In the terminal, *left*-click on `http://0.0.0.0:8080/` and select **Open**.

4. Select **Database to query**

   **Original**: Fetch data directly from Pubmed (same as **Version 1**).

   **Extracts from original**: Fetch data from DBF - Note **Warning** above.
