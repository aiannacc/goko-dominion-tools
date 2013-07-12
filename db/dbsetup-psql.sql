DROP TABLE IF EXISTS advbot;
CREATE TABLE advbot (
  pname varchar(100) DEFAULT NULL,
  PRIMARY KEY(pname)
);

DROP TABLE IF EXISTS bot;
CREATE TABLE bot (
  pname varchar(100) NOT NULL,
  PRIMARY KEY(pname)
);

DROP TABLE IF EXISTS tester;
CREATE TABLE tester (
  pname varchar(100) NOT NULL,
  PRIMARY KEY(pname)
);

DROP TABLE IF EXISTS rating;
CREATE TABLE rating (
  time timestamp NOT NULL,
  rank smallint NOT NULL,
  pname varchar(50) NOT NULL,
  rating smallint NOT NULL
);
CREATE UNIQUE INDEX rating_pt_idx ON rating (pname,time);
CREATE INDEX rating_p_idx ON rating (pname);
CREATE INDEX rating_r_idx ON rating (rank);

DROP TABLE IF EXISTS game;
CREATE TABLE game (
  time timestamp NOT NULL,
  logfile varchar(50) NOT NULL,
  supply varchar(500) NOT NULL,
  colony boolean NOT NULL,
  shelters boolean NOT NULL,
  pcount smallint NOT NULL,
  plist varchar(500) NOT NULL,
  bot boolean NOT NULL,
  guest boolean NOT NULL,
  rating varchar(10) DEFAULT NULL,
  adventure boolean NOT NULL,
  dup_supply boolean DEFAULT NULL,
  PRIMARY KEY(logfile)
);
CREATE INDEX game_t_idx ON game (time);
CREATE INDEX game_su_idx ON game (supply);
CREATE INDEX game_c_idx ON game (colony);
CREATE INDEX game_sh_idx ON game (shelters);
CREATE INDEX game_pc_idx ON game (pcount);
CREATE INDEX game_pl_idx ON game (plist);
CREATE INDEX game_b_idx ON game (bot);
CREATE INDEX game_g_idx ON game (guest);
CREATE INDEX game_r_idx ON game (rating);
CREATE INDEX game_a_idx ON game (adventure);
CREATE INDEX game_ds_idx ON game (dup_supply);

DROP TABLE IF EXISTS presult;
CREATE TABLE presult (
  pname varchar(50) NOT NULL,
  vps smallint NOT NULL,
  turns smallint NOT NULL,
  rank smallint NOT NULL,
  quit boolean NOT NULL,
  turnorder smallint DEFAULT NULL,
  resign boolean NOT NULL,
  logfile varchar(50) NOT NULL,
  pcount smallint NOT NULL,
  PRIMARY KEY(logfile,pname)
); 
CREATE INDEX presult_r_idx ON presult (rank);
CREATE INDEX presult_p_idx ON presult (pname);
CREATE INDEX presult_pc_idx ON presult (pcount);
CREATE INDEX presult_l_idx ON presult (logfile);

DROP TABLE IF EXISTS ret;
CREATE TABLE ret (
  logfile varchar(50) NOT NULL,
  cname varchar(30) NOT NULL,
  cpile varchar(30) NOT NULL,
  pname varchar(50) NOT NULL,
  turn smallint NOT NULL
);
CREATE INDEX ret_l_idx ON ret (logfile);
CREATE INDEX ret_c_idx ON ret (cname);
CREATE INDEX ret_cp_idx ON ret (cpile);
CREATE INDEX ret_p_idx ON ret (pname);
CREATE INDEX ret_t_idx ON ret (turn);

DROP TABLE IF EXISTS gain;
CREATE TABLE gain (
  logfile varchar(50) NOT NULL,
  cname varchar(30) NOT NULL,
  cpile varchar(30) NOT NULL,
  pname varchar(50) NOT NULL,
  turn smallint NOT NULL
);
CREATE INDEX gain_l_idx ON ret (logfile);
CREATE INDEX gain_c_idx ON gain (cname);
CREATE INDEX gain_cp_idx ON gain (cpile);
CREATE INDEX gain_p_idx ON gain (pname);
CREATE INDEX gain_t_idx ON gain (turn);

DROP TABLE IF EXISTS temp_adv_opp;
CREATE TABLE temp_adv_opp (
    pname varchar(50) NOT NULL,
    PRIMARY KEY(pname)
);

DROP TABLE IF EXISTS temp_adv_player;
CREATE TABLE temp_adv_player (
    pname varchar(50) NOT NULL,
    PRIMARY KEY(pname)
);
