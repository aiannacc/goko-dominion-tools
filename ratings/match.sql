USE dominionlogs;

DROP VIEW IF EXISTS temp_r;
CREATE VIEW temp_r
   AS SELECT player,time,rating 
        FROM ratings 
       ORDER BY player,time;

DROP TABLE IF EXISTS temp_ri;
CREATE TABLE temp_ri
   AS SELECT r.*,(@n:=@n+1) as i
        FROM temp_r as r,(SELECT @n:=0) as x;

SELECT * from temp_ri LIMIT 10;


/*
SELECT * INTO OUTFILE '/tmp/matches.csv'
              FIELDS TERMINATED BY ','
              LINES TERMINATED BY '\n'
         FROM matches;
*/
       
