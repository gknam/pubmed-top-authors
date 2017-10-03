# pubmed-top-authors
Find authors on Pubmed who published most (1) on a keyword or (2) together with an author.
Then draw graphs on their publication records per year and per journal.

# Get started
Make an account at [Cloud9](https://c9.io), and [create a workspace](https://docs.c9.io/v1.0/docs/create-a-workspace) choosing **Python** as a template.

Then, download repository.

`git clone https://github.com/gknam/pubmed-top-authors.git`

Go into the repository.

`cd pubmed-top-authors`

Change the default python version to 3.4

`sudo ln -sfn python3.4 /usr/bin/python`

Install required packages

`sudo pip install -r requirements.txt`

Setup Flask.

`export FLASK_APP=application.py`

`export FLASK_DEBUG=1`

Now, there are two versions of this website.

### Version 1
*All data are fetched directly from Pubmed.*

Go to the branch for this version.

`git checkout original_only`

Initiate server.

`flask run --host=0.0.0.0 --port=8080`

Open website: In the terminal, left-click on `http://0.0.0.0:8080/` and select **Open**.

### Version 2
*Data are fetched from a database file in this website's server. When the server starts, data are constantly
fetched from Pubmed and saved into the database file in the background.*

Go to the branch for this version.

`git checkout master`

Initiate server.

`flask run --no-reload --host=0.0.0.0 --port=8080`

Open website: In the terminal, left-click on `http://0.0.0.0:8080/` and select **Open**.


**Warning**: The database file (**database/pubmed.db**) is initially empty, and complete update of the database file is assumed to take a few months.
