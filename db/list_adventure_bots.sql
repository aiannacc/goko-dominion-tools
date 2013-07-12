/* Generates a complete list of opponents in Goko's adventure mode.
 *
 * Designed for determining whether old logs that don't specify the rating
 * system were played in Goko's Adventure mode or not. Needs a large number of
 * known adventure games to already be in the database. Assumes that we have
 * at least one game against each adventure bot (well, actually it assumes a
 * little more, but I don't know how to say it rigorously without graph
 * theory).
 *
 * Written in May 2013, modified without rerunning in July 2013. Might be
 * buggy. I think I originally ran this on a MySQL database, but it have been
 * PostGRE.
 */ 

/* Constructs a table of player names from 2-player adventure games */
DROP TABLE IF EXISTS temp_adv_match2;
CREATE TABLE temp_adv_match2 AS
      SELECT DISTINCT a.pname AS p1, b.pname AS p2 
        FROM game g
        JOIN presult a USING(logfile)
        JOIN presult b USING(logfile)
       WHERE g.rating='adventure'
         AND a.pname<b.pname
         AND a.pcount=2;

/* Known human players. To be grown iteratively. */
DROP TABLE IF EXISTS temp_adv_player;
CREATE TABLE temp_adv_player pname (VARCHAR(50));

/* Known adventure opponents (bots). To be grown iteratively. */
DROP TABLE IF EXISTS temp_adv_opp;
CREATE TABLE temp_adv_opp pname (VARCHAR(50));
INSERT INTO temp_adv_opp VALUES ('Lady Elena'); /* Seed value */

/* Anyone who has played a 2-player game with 'Lady Elena' is a human. */
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);

/* Anyone who has played a 2-player game a human is a bot. */
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);

/* Repeat 3 times. */
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);

/* 
 * NOTE: Three iterations is enough with my database. It might not be enough if
 * a smaller seed database of known adventure games is used.
 */

/* Some adventure opponents only play in 3+ player games */
DROP TABLE IF EXISTS temp_adv_match3456;
CREATE TABLE temp_adv_match3456 AS
      SELECT DISTINCT a.pname AS p1, b.pname AS p2 
        FROM game g
        JOIN presult a USING(logfile)
        JOIN presult b USING(logfile)
       WHERE g.rating='adventure'
         AND a.pname<b.pname
         AND a.pcount>2;

/* Anyone in a 3+ player game with a human is a bot. */
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match3456 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);

/* NOTE: The table of adventure opponent bots is now complete. */
RENAME TABLE temp_adv_opp TO adventure_opponents;

/* Clean up temp tables. */
DROP TABLE IF EXISTS temp_adv_player;
DROP TABLE IF EXISTS temp_adv_match2;
DROP TABLE IF EXISTS temp_adv_match3456;

/* Use this information to update existing game info if necessary. */
/*
UPDATE game g
   SET rating='x'
  FROM presult p, adventure_opponents  o
 WHERE g.rating IS NOT NULL
   AND g.logfile = p.logfile
   AND p.pname=o.pname;
*/
