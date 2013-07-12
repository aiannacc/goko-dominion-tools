goko-dominion-tools
===================

Tools for use with [Goko's online Dominion game](play.goko.com/Dominion/gameClient.html).

Features:

- Log Parsing/Database
- Log Search
- Kingdom Visualizer
- Leaderboard scraping

Work in Progress:

- Automatch browser extension
- alternative rating systems
- Goko ratings analysis

Contributions are welcome.

### Installation

You'll need Python v3.3.2+ and the following PyPi packages:

- beautifulsoup4 (4.2.1)
- bidict (0.1.1)
- py-postgresql (1.1.0)
- tornado (3.1)

You can either connect to a remote database of parsed games or create your own. To create your own, you'll also need PostgreSQL. The log download and parsing script requires a \*NIX environment with bash, perl, zcat, split, and wget.

### Database Setup

#### Remote

The default configuration is to connect to the PostgreSQL server at gokologs.drunkensailor.org, which has all the games played on Goko and updates every 15 minutes.

This is the same machine that hosts the log search and kingdom visualizer. If you want to run something that's really IO-intensive, like dumping the whole DB to your own machine, please let me know first.

#### Local

To create your own database, install PostgreSQL and create a database with UTF-8 encoding. Then create the database schema:

    $ psql -d goko < db/schema.sql

To download and parse logs from the Goko log archive: 

    $ bash logparse/dbupdate.sh <logdir> <codebase> <dates>

where `<logdir>` is the local directory where you want to store unparsed logs, `<codebase>` is this project's root, and `<dates>` are formatted like YYYYMMDD.

Games before May 13, 2013 don't include rating system information, but we can deduce which games were played in 'adventure' mode using the names of the players:

    $ psql -d goko < db/list_adventure_bots.sql

### Server setup

You can run the log search and kingdom visualizer server like:

    $ python logsearch/requesthandler.py <port>
