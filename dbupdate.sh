#/bin/bash

# Usage:   dbupdate <dates...>
# Example: dbupdate 20130614
# Example: dbupdate 20130614 20130501
# Example: dbupdate 201306*
#
# Downloads game logs for the given day, then parses them into the database.
# Skips download for logs that already exist locally. Skips import for logs
# that are already in the database.
#
# This downloads about 4x faster than the Python code I originally wrote. I
# don't know why. If I figure it out, I'll do it in Python instead.
#
# Thanks to nutki on forum.dominionstrategy.com for an example script showing
# how to download logs with wget.
#
while [ $# -gt 0 ]
do
    echo "Day: $1"

    BASE=http://dominionlogs.goko.com/$1/
    THREADS=20
    LOGDIR=/mnt/raid/media/dominion/logs
    CODEDIR="`pwd`"

    # Create log file directory
    cd "$LOGDIR"
    [ -d "$1" ] || mkdir "$1"
    cd "$1"
    [ -f "*.gz" ] && rm *.gz
    [ -f "_*" ] && rm _*

    # Get list of logs on server
    wget --header='Accept-Encoding: gzip' $BASE -O- 2>/dev/null |
        zcat | perl -lne 'print "$1" if /href="(.*?txt)"/' > _all
    echo "`cat _all | wc -l` logs on server"

    # Distinguish old logs vs. new
    ls > _old
    ls _* >> _old
    cat _all _old _old | sort | uniq -u > _new
    echo "Downloading `cat _new | wc -l` logs from server"

    # Download new logs in threads
    if [ `cat _new | wc -l` -gt 0 ]
    then
        cat _new | split -l 100 - _index.
        ls _index.* | xargs -n 1 -P $THREADS wget -nc \
            --base=$BASE --header='Accept-Encoding: gzip' -i 2>/dev/null
        rm _index.*
    fi

    # Clean up
    [ -f _all ] && rm _all
    [ -f _old ] && rm _old
    [ -f _new ] && rm _new

    # Parse new logs into database
    cd $CODEDIR/logparse
    ./log2db.py "$LOGDIR"/$1
    
    shift
done
