# pubmed-top-authors
Find authors on Pubmed who published most (1) on a keyword or (2) together with an author.
Then draw graphs on their publication records per year and per journal.

# Get started
Make an account at https://c9.io. Then, create an environment and open a terminal.

Download codes from this repository

`git clone https://github.com/gknam/pubmed-top-authors.git`

`cd pubmed-top-authors`

Change the default python version to 3.4

`sudo ln -sfn python3.4 /usr/bin/python`

Install required packages

`sudo pip install -r requirements.txt`

Setup Flask

`export FLASK_APP=application.py`

`export FLASK_DEBUG=1`




Now, there are two versions of this website.

### Version 1
All data are fetchd directly from Pubmed.

`git checkout original_only`

`flask run --host=0.0.0.0 --port=8080`



### Version 2
Data are fetched from a database file in this website's server. When the server starts, data are constantly
fetched from Pubmed and saved into the database file in the background.

`git checkout master`

`flask run --no-reload --host=0.0.0.0 --port=8080`

Warning: The database file is initially empty, and complete update of the database file is assumed to take a few months.
