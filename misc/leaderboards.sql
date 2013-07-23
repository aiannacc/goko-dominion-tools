DROP table if exists temp_rcomp;
CREATE table temp_rcomp AS
SELECT pname, mu as r0, mu - sigma as r1, mu - 2*sigma as r2, mu - 3*sigma as r3, mu-50*sigma as r50, mu-500*sigma as r500
  FROM ts_rating;

SELECT * from temp_rcomp order by r0 desc limit 100;
SELECT * from temp_rcomp order by r1 desc limit 100;
SELECT * from temp_rcomp order by r2 desc limit 100;
SELECT * from temp_rcomp order by r3 desc limit 100;
SELECT * from temp_rcomp order by r50 desc limit 100;
SELECT * from temp_rcomp order by r500 desc limit 100;

select pname, mu - 250 * mu as r from ts_rating order by r desc limit 25;
