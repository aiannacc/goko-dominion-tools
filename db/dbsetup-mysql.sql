DROP TABLE IF EXISTS `advopps`;
CREATE TABLE `advopps` (
  `pname` varchar(100) DEFAULT NULL,
  PRIMARY KEY(`pname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `bots`;
CREATE TABLE `bots` (
  `pname` varchar(100) NOT NULL,
  PRIMARY KEY(`pname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `testers`;
CREATE TABLE `testers` (
  `pname` varchar(100) NOT NULL,
  PRIMARY KEY(`pname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `ratings`;
CREATE TABLE `ratings` (
  `time` datetime DEFAULT NULL,
  `rank` int(11) DEFAULT NULL,
  `pname` varchar(50) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `game`;
CREATE TABLE `game` (
  `time` datetime NOT NULL,
  `logfile` varchar(50) NOT NULL,
  `logttext` blob NOT NULL,
  `bot` tinyint(1) NOT NULL,
  `guest` tinyint(1) NOT NULL,
  `rating` tinyint(1) DEFAULT NULL,
  `pcount` int(11) NOT NULL,
  `colony` tinyint(1) NOT NULL,
  `shelters` tinyint(1) NOT NULL,
  PRIMARY KEY (`logfile`),
  KEY search_idx (`pcount`,`bot`,`guest`,`colony`,`shelters`,`rating`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `presult`;
CREATE TABLE `presult` (
  `pname` varchar(50) NOT NULL,
  `vps` int(11) NOT NULL,
  `turns` int(11) NOT NULL,
  `rank` int(11) NOT NULL,
  `quit` tinyint(1) NOT NULL,
  `turnorder` int(11) DEFAULT NULL,
  `resign` tinyint(1) NOT NULL,
  `logfile` varchar(50) NOT NULL,
  KEY `logfile` (`logfile`),
  KEY `pr_idx` (`pname`,`rank`),
  KEY `rp_idx` (`rank`,`pname`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
