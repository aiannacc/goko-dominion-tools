goko-dominion-tools
===================

Tools for use with [Goko's online Dominion game](https://play.goko.com/Dominion/gameClient.html).

Features:

- Log Parsing/Database
- Log Search
- Kingdom Visualizer
- Trueskill Leaderboard

Work in Progress:

- Automatch browser extension

Contributions are welcome.

### Installation (out of date)

You'll need Python v3.3.2+ and the following PyPi packages:

- beautifulsoup4 (4.2.1)
- bidict (0.1.1)
- numpy (1.7.1)
- py-postgresql (1.1.0)
- pytz (2013b)
- scipy (0.12.0)
- tornado (3.1)
- trueskill (0.4.1)

You can either connect to a remote database of parsed games or create your own. To create your own, you'll also need PostgreSQL. The log download and parsing script requires a \*NIX environment with bash, perl, zcat, split, and wget.

### Database Setup

#### Remote

The default configuration is to connect to the PostgreSQL server at gokologs.drunkensailor.org, which has all the games played on Goko and updates every 15 minutes. Configuration information is in `gdt/model/db_manager`.

#### Local (out of date)

To create your own database, install PostgreSQL and create a database with UTF-8 encoding. Then create the database schema:

    $ psql -d goko < misc/db/schema.sql

Import the non-game info into your database (bot names, etc):

    $ psql -d goko < misc/db_initdata/*

Download and parse logs from the Goko log archive: 

    $ bash update_logdb.sh <logdir> <codebase> <dates>

where `<logdir>` is the local directory where you want to store unparsed logs, `<codebase>` is this project's root, and `<dates>` are formatted like YYYYMMDD. You'll have to run this for each day. The import process is IO-bound on a modern machine. An SSD drive helps a lot. As of July 2013, the full database is about 100G.


### Server setup (out of date)

Start the server:

    $ python ./start_server.py <port>

Go to http://localhost:<port> to use the logsearch, kingdom visualizer, and leaderboard. The automatch server runs on the same port but has no UI.
