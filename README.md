# pubmed-top-authors
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

1. Go to the branch for this version.

   `git checkout original_only`

2. Initiate server.

   `flask run --host=0.0.0.0 --port=8080`

3. Open website

   In the terminal, *left*-click on `http://0.0.0.0:8080/` and select **Open**.



## Kill server

To kill the server, do the following with the the **terminal in which** `flask` **command is running**.

* Click anywhere in the terminal and press `Ctrl` + `C`.
* Close the terminal

If you want to restart the server, follow the instructions in **Start server** section above.

*You might want to kill the server and restart it in case you want to stop a search and do a new one. Search will be slower with bigger numbers typed in "Max number of days from today and/or "Max number of articles to check" on the website.*

# 2. Technical note
All data are fetched directly from Pubmed via [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/).
