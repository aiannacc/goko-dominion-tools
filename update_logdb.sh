#/bin/bash

USAGE='dbupdate <logdir> <codebase> <dates...>'

# Downloads game logs for the given day, then parses them into the database.
# Skips download for logs that already exist locally. Skips import for logs
# that are already in the database.
#
# This downloads about 4x faster than the Python code I originally wrote. I
# don't know why. If I figure it out, I'll do it in Python instead.
#
# Example: dbupdate ~/gokologs/ ~/code/goko-dominion-tools/ 20130614
# Example: dbupdate ~/gokologs/ ~/code/goko-dominion-tools/ 20130614 20130615
#
# TODO: Verify arguments

# Default logdir and codebase when run on AI's server
if [ `hostname` = "iron" ]
then
    LOGDIR=/mnt/raid/media/dominion/logs/
else
    LOGDIR="$1"
    shift
fi

# Default to today's date
if [ $# -eq 0 ]
then
   set -- `date +%Y%m%d`
fi

codedir="`pwd`"

# Iterate over all given dates
while [ $# -gt 0 ]
do
    # TODO: verify that arguments are dates and properly formatted

    echo "Day: $1"

    BASE=http://dominionlogs.goko.com/$1/
    THREADS=20

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
    cd $codedir
    python log2db.py "$LOGDIR"/$1
    
    shift
done
