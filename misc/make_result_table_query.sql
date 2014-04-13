insert into game_result (
select g.time, g.logfile, g.pcount, g.guest, g.bot,
       LEAST(p1.turns, p2.turns, p3.turns, p4.turns, p5.turns, p6.turns),
       p1.rank,
       p2.rank,
       p3.rank,
       p4.rank,
       p5.rank,
       p6.rank,
       p1.pname, 
       p2.pname, 
       p3.pname, 
       p4.pname, 
       p5.pname, 
       p6.pname
  from game g
  join presult p1 using(logfile)
  join presult p2 using(logfile)
  join presult p3 using(logfile)
  join presult p4 using(logfile)
  join presult p5 using(logfile)
  join presult p6 using(logfile)
 where g.pcount=6
   and p1.pname>p2.pname
   and p2.pname>p3.pname
   and p3.pname>p4.pname
   and p4.pname>p5.pname
   and p5.pname>p6.pname
);

insert into game_result (
select g.time, g.logfile, g.pcount, g.guest, g.bot,
       LEAST(p1.turns, p2.turns, p3.turns, p4.turns, p5.turns),
       p1.rank,
       p2.rank,
       p3.rank,
       p4.rank,
       p5.rank,
       NULL,
       p1.pname, 
       p2.pname, 
       p3.pname, 
       p4.pname, 
       p5.pname,
       NULL
  from game g
  join presult p1 using(logfile)
  join presult p2 using(logfile)
  join presult p3 using(logfile)
  join presult p4 using(logfile)
  join presult p5 using(logfile)
 where g.pcount=5
   and p1.pname>p2.pname
   and p2.pname>p3.pname
   and p3.pname>p4.pname
   and p4.pname>p5.pname
);

insert into game_result (
select g.time, g.logfile, g.pcount, g.guest, g.bot,
       LEAST(p1.turns, p2.turns, p3.turns, p4.turns),
       p1.rank,
       p2.rank,
       p3.rank,
       p4.rank,
       NULL,
       NULL,
       p1.pname,
       p2.pname,
       p3.pname,
       p4.pname,
       NULL,
       NULL
  from game g
  join presult p1 using(logfile)
  join presult p2 using(logfile)
  join presult p3 using(logfile)
  join presult p4 using(logfile)
 where g.pcount=4
   and p1.pname>p2.pname
   and p2.pname>p3.pname
   and p3.pname>p4.pname
);

insert into game_result (
select g.time, g.logfile, g.pcount, g.guest, g.bot,
       LEAST(p1.turns, p2.turns, p3.turns),
       p1.rank,
       p2.rank,
       p3.rank,
       NULL,
       NULL,
       NULL,
       p1.pname, 
       p2.pname, 
       p3.pname,
       NULL,
       NULL,
       NULL
  from game g
  join presult p1 using(logfile)
  join presult p2 using(logfile)
  join presult p3 using(logfile)
 where g.pcount=3
   and p1.pname>p2.pname
   and p2.pname>p3.pname
);

insert into game_result (
select g.time, g.logfile, g.pcount, g.guest, g.bot,
       LEAST(p1.turns, p2.turns),
       p1.rank,
       p2.rank, 
       NULL,
       NULL,
       NULL,
       NULL,
       p1.pname,
       p2.pname,
       NULL,
       NULL,
       NULL,
       NULL
  from game g
  join presult p1 using(logfile)
  join presult p2 using(logfile)
 where g.pcount=2
   and p1.pname>p2.pname
);
