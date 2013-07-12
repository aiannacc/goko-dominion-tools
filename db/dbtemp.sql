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
