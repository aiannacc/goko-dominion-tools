/*
DROP TABLE IF EXISTS temp_adv_match2;
CREATE TABLE temp_adv_match2 AS
      SELECT DISTINCT a.pname AS p1, b.pname AS p2 
        FROM game g
        JOIN presult a USING(logfile)
        JOIN presult b USING(logfile)
       WHERE g.rating='adventure'
         AND a.pname<b.pname
         AND a.pcount=2;

DROP TABLE IF EXISTS temp_adv_match3456;
CREATE TABLE temp_adv_match3456 AS
      SELECT DISTINCT a.pname AS p1, b.pname AS p2 
        FROM game g
        JOIN presult a USING(logfile)
        JOIN presult b USING(logfile)
       WHERE g.rating='adventure'
         AND a.pname<b.pname
         AND a.pcount!=2;
*/

DELETE FROM temp_adv_opp;
DELETE FROM temp_adv_player;

INSERT INTO temp_adv_opp VALUES ('Lady Elena');

INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);
INSERT INTO temp_adv_player (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_opp o ON m.p2=o.pname) EXCEPT (SELECT pname FROM temp_adv_player);
INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match2 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);

INSERT INTO temp_adv_opp (SELECT distinct m.p1 AS pname FROM temp_adv_match3456 m JOIN temp_adv_player p ON m.p2=p.pname) EXCEPT (SELECT pname FROM temp_adv_opp);

/* Use what we know to update game info */
UPDATE game g
   SET rating='x'
  FROM presult p, temp_adv_opp o
 WHERE g.rating IS NOT NULL
   AND g.logfile = p.logfile
   AND p.pname=o.pname;
