--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: advbot; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE advbot (
    pname character varying(50)
);


ALTER TABLE public.advbot OWNER TO ai;

--
-- Name: bot; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE bot (
    pname character varying(100) NOT NULL
);


ALTER TABLE public.bot OWNER TO ai;

--
-- Name: card_url; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE card_url (
    card character varying(30) NOT NULL,
    url character varying(200) NOT NULL
);


ALTER TABLE public.card_url OWNER TO ai;

--
-- Name: gain; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE gain (
    logfile character varying(50) NOT NULL,
    cname character varying(30) NOT NULL,
    cpile character varying(30) NOT NULL,
    pname character varying(50) NOT NULL,
    turn smallint NOT NULL
);


ALTER TABLE public.gain OWNER TO ai;

--
-- Name: game; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE game (
    "time" timestamp without time zone NOT NULL,
    logfile character varying(50) NOT NULL,
    supply character varying(500) NOT NULL,
    colony boolean NOT NULL,
    shelters boolean NOT NULL,
    pcount smallint NOT NULL,
    plist character varying(500) NOT NULL,
    bot boolean NOT NULL,
    guest boolean NOT NULL,
    rating character varying(10) DEFAULT NULL::character varying,
    adventure boolean NOT NULL,
    dup_supply boolean
);


ALTER TABLE public.game OWNER TO ai;

--
-- Name: old_rating; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE old_rating (
    "time" timestamp without time zone NOT NULL,
    rank smallint NOT NULL,
    pname character varying(50) NOT NULL,
    rating smallint NOT NULL
);


ALTER TABLE public.old_rating OWNER TO ai;

--
-- Name: phash; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE phash (
    pname character varying(50),
    phash text
);


ALTER TABLE public.phash OWNER TO ai;

--
-- Name: presult; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE presult (
    pname character varying(50) NOT NULL,
    vps smallint NOT NULL,
    turns smallint NOT NULL,
    rank smallint NOT NULL,
    quit boolean NOT NULL,
    turnorder smallint,
    resign boolean NOT NULL,
    logfile character varying(50) NOT NULL,
    pcount smallint NOT NULL,
    pname_lower character varying(50)
);


ALTER TABLE public.presult OWNER TO ai;

--
-- Name: ret; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ret (
    logfile character varying(50) NOT NULL,
    cname character varying(30) NOT NULL,
    cpile character varying(30) NOT NULL,
    pname character varying(50) NOT NULL,
    turn smallint NOT NULL
);


ALTER TABLE public.ret OWNER TO ai;

--
-- Name: temp_rcomp; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE temp_rcomp (
    pname character varying(50),
    r0 numeric(6,4),
    r1 numeric,
    r2 numeric,
    r3 numeric,
    r50 numeric,
    r500 numeric
);


ALTER TABLE public.temp_rcomp OWNER TO ai;

--
-- Name: ts_rating; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ts_rating (
    "time" timestamp without time zone,
    logfile character varying(50),
    pname character varying(50),
    mu numeric(6,4),
    sigma numeric(6,4),
    numgames integer,
    level_m3s numeric(6,4)
);


ALTER TABLE public.ts_rating OWNER TO ai;

--
-- Name: ts_rating_history; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ts_rating_history (
    "time" timestamp without time zone,
    logfile character varying(50),
    pname character varying(50),
    old_mu numeric(6,4),
    old_sigma numeric(6,4),
    old_opp_mu numeric(6,4),
    old_opp_sigma numeric(6,4),
    new_mu numeric(6,4),
    new_sigma numeric(6,4)
);


ALTER TABLE public.ts_rating_history OWNER TO ai;

--
-- Name: ts_rating_history_old; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ts_rating_history_old (
    "time" timestamp without time zone,
    logfile character varying(50),
    pname character varying(50),
    old_mu numeric(6,4),
    old_sigma numeric(6,4),
    old_opp_mu numeric(6,4),
    old_opp_sigma numeric(6,4),
    new_mu numeric(6,4),
    new_sigma numeric(6,4)
);


ALTER TABLE public.ts_rating_history_old OWNER TO ai;

--
-- Name: ts_rating_old; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ts_rating_old (
    "time" timestamp without time zone,
    logfile character varying(50),
    pname character varying(50),
    mu numeric(6,4),
    sigma numeric(6,4)
);


ALTER TABLE public.ts_rating_old OWNER TO ai;

--
-- Name: ts_state; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ts_state (
    system character varying(50) NOT NULL,
    pname character varying(50) NOT NULL,
    mu numeric(6,4) NOT NULL,
    sigma numeric(6,4) NOT NULL,
    last_game_time time without time zone NOT NULL,
    num_games integer NOT NULL,
    last_log character varying(80) NOT NULL
);


ALTER TABLE public.ts_state OWNER TO ai;

--
-- Name: ts_system; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE ts_system (
    name character varying(50) NOT NULL,
    mu0 double precision,
    sigma0 double precision,
    beta double precision,
    tau double precision,
    draw_prob double precision,
    sigma_reversion double precision
);


ALTER TABLE public.ts_system OWNER TO ai;

--
-- Name: bot_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY bot
    ADD CONSTRAINT bot_pkey PRIMARY KEY (pname);


--
-- Name: card_url_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY card_url
    ADD CONSTRAINT card_url_pkey PRIMARY KEY (card);


--
-- Name: game_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY game
    ADD CONSTRAINT game_pkey PRIMARY KEY (logfile);


--
-- Name: presult_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY presult
    ADD CONSTRAINT presult_pkey PRIMARY KEY (logfile, pname);


--
-- Name: rating_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY ts_state
    ADD CONSTRAINT rating_pkey PRIMARY KEY (system, pname);


--
-- Name: ts_system_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY ts_system
    ADD CONSTRAINT ts_system_pkey PRIMARY KEY (name);


--
-- Name: gain_c_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gain_c_idx ON gain USING btree (cname);


--
-- Name: gain_cp_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gain_cp_idx ON gain USING btree (cpile);


--
-- Name: gain_l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gain_l_idx ON ret USING btree (logfile);


--
-- Name: gain_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gain_p_idx ON gain USING btree (pname);


--
-- Name: gain_t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gain_t_idx ON gain USING btree (turn);


--
-- Name: game_a_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_a_idx ON game USING btree (adventure);


--
-- Name: game_b_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_b_idx ON game USING btree (bot);


--
-- Name: game_c_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_c_idx ON game USING btree (colony);


--
-- Name: game_ds_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_ds_idx ON game USING btree (dup_supply);


--
-- Name: game_g_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_g_idx ON game USING btree (guest);


--
-- Name: game_pc_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_pc_idx ON game USING btree (pcount);


--
-- Name: game_pl_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_pl_idx ON game USING btree (plist);


--
-- Name: game_r_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_r_idx ON game USING btree (rating);


--
-- Name: game_sh_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_sh_idx ON game USING btree (shelters);


--
-- Name: game_su_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_su_idx ON game USING btree (supply);


--
-- Name: game_t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX game_t_idx ON game USING btree ("time");


--
-- Name: l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX l_idx ON ts_rating_old USING btree (logfile);


--
-- Name: p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE UNIQUE INDEX p_idx ON ts_rating_old USING btree (pname);


--
-- Name: presult_l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX presult_l_idx ON presult USING btree (logfile);


--
-- Name: presult_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX presult_p_idx ON presult USING btree (pname);


--
-- Name: presult_pc_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX presult_pc_idx ON presult USING btree (pcount);


--
-- Name: presult_pl_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX presult_pl_idx ON presult USING btree (pname_lower);


--
-- Name: presult_r_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX presult_r_idx ON presult USING btree (rank);


--
-- Name: rating_last_game_time_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_last_game_time_idx ON ts_state USING btree (last_game_time);


--
-- Name: rating_logfile_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_logfile_idx ON ts_state USING btree (last_log);


--
-- Name: rating_mu_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_mu_idx ON ts_state USING btree (mu);


--
-- Name: rating_num_games_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_num_games_idx ON ts_state USING btree (num_games);


--
-- Name: rating_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_p_idx ON old_rating USING btree (pname);


--
-- Name: rating_pt_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE UNIQUE INDEX rating_pt_idx ON old_rating USING btree (pname, "time");


--
-- Name: rating_r_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_r_idx ON old_rating USING btree (rank);


--
-- Name: rating_sigma_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX rating_sigma_idx ON ts_state USING btree (sigma);


--
-- Name: ret_c_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX ret_c_idx ON ret USING btree (cname);


--
-- Name: ret_cp_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX ret_cp_idx ON ret USING btree (cpile);


--
-- Name: ret_l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX ret_l_idx ON ret USING btree (logfile);


--
-- Name: ret_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX ret_p_idx ON ret USING btree (pname);


--
-- Name: ret_t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX ret_t_idx ON ret USING btree (turn);


--
-- Name: t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX t_idx ON ts_rating_old USING btree ("time");


--
-- Name: tsr_l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsr_l_idx ON ts_rating USING btree (logfile);


--
-- Name: tsr_n_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsr_n_idx ON ts_rating USING btree (numgames);


--
-- Name: tsr_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsr_p_idx ON ts_rating USING btree (pname);


--
-- Name: tsr_t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsr_t_idx ON ts_rating USING btree ("time");


--
-- Name: tsrh_l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsrh_l_idx ON ts_rating_history USING btree (logfile);


--
-- Name: tsrh_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsrh_p_idx ON ts_rating_history USING btree (pname);


--
-- Name: tsrh_pl_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE UNIQUE INDEX tsrh_pl_idx ON ts_rating_history USING btree (pname, logfile);


--
-- Name: tsrh_t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsrh_t_idx ON ts_rating_history USING btree ("time");


--
-- Name: tsrhist_l_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsrhist_l_idx ON ts_rating_history_old USING btree (logfile);


--
-- Name: tsrhist_p_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsrhist_p_idx ON ts_rating_history_old USING btree (pname);


--
-- Name: tsrhist_pl_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE UNIQUE INDEX tsrhist_pl_idx ON ts_rating_history_old USING btree (pname, logfile);


--
-- Name: tsrhist_t_idx; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX tsrhist_t_idx ON ts_rating_history_old USING btree ("time");


--
-- Name: rating_system_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ai
--

ALTER TABLE ONLY ts_state
    ADD CONSTRAINT rating_system_fkey FOREIGN KEY (system) REFERENCES ts_system(name);


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: advbot; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY advbot (pname) FROM stdin;
Lady Elena
Gentleman Preston
Gentleman Earl
Gentleman Ivan
Gentleman Donald
Captain Althea
Gentleman Gandolf
Cardwell the Serf
Gentleman Winston
Gentleman Drake
Gentleman Morell
Gentleman Ashton
Gavin the Terrible
Gentleman Searle
Gentleman Faran
Dragon
Bonifacius
Gentleman Althalos
Grandfather
Gentleman Garrick
Gentleman Russell
Gentleman Viktor
Gentleman Charles
Jeeves
Gentleman Albert
Gentleman Norman
Gentleman Vilin
Gentleman Tristan
Gentleman Bradshaw
Gentleman Egric
Ela
Gentleman Osric
Gentleman Ingvar
King Rex
Alice the Serf
Gentleman Eduardo
King Leonard
Gentleman Justin
Gentleman Keaton
Gentleman Akelin
Baroness Paulina
Gentleman Harald
Gentleman Thrall
Gentleman Hal
Egbert
Gentleman Alvar
Gentleman Sedgewick
Gentleman Benjamin
Cadby
Drusilla
Galore, the Mountebank
Joseph Gelu
Jewel Owner
Grandmother
Archer
Belinda
Ghost Gavin
Edith
Gentleman Pierson
Henrietta
Gentleman Davidson
Distant Cousin
Gentleman Walter
Barnabas
Concealed Employer
\.


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: bot; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY bot (pname) FROM stdin;
Conqueror Bot
Lord Bottington
Banker Bot
Villager Bot
Village Idiot Bot
Serf Bot
Defender Bot
Warlord Bot
\.


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: card_url; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY card_url (card, url) FROM stdin;
JackOfAllTrades	http://wiki.dominionstrategy.com/images/3/38/Jack_of_all_Trades.jpg
Knights	http://wiki.dominionstrategy.com/images/9/9a/Knights.jpg
Abandoned Mine	http://wiki.dominionstrategy.com/images/6/6d/Abandoned_Mine.jpg
Adventurer	http://wiki.dominionstrategy.com/images/7/71/Adventurer.jpg
Advisor	http://wiki.dominionstrategy.com/images/5/5e/Advisor.jpg
Alchemist	http://wiki.dominionstrategy.com/images/2/22/Alchemist.jpg
Altar	http://wiki.dominionstrategy.com/images/b/b3/Altar.jpg
Ambassador	http://wiki.dominionstrategy.com/images/7/74/Ambassador.jpg
Apothecary	http://wiki.dominionstrategy.com/images/6/69/Apothecary.jpg
Apprentice	http://wiki.dominionstrategy.com/images/2/20/Apprentice.jpg
Armory	http://wiki.dominionstrategy.com/images/a/a7/Armory.jpg
Bag of Gold	http://wiki.dominionstrategy.com/images/b/b4/Bag_of_Gold.jpg
Baker	http://wiki.dominionstrategy.com/images/b/b9/Baker.jpg
Band of Misfits	http://wiki.dominionstrategy.com/images/5/51/Band_of_Misfits.jpg
Bandit Camp	http://wiki.dominionstrategy.com/images/4/43/Bandit_Camp.jpg
Bank	http://wiki.dominionstrategy.com/images/7/78/Bank.jpg
Baron	http://wiki.dominionstrategy.com/images/7/73/Baron.jpg
Bazaar	http://wiki.dominionstrategy.com/images/f/f7/Bazaar.jpg
Beggar	http://wiki.dominionstrategy.com/images/2/2f/Beggar.jpg
Bishop	http://wiki.dominionstrategy.com/images/b/b4/Bishop.jpg
Black Market	http://wiki.dominionstrategy.com/images/f/fa/Black_Market.jpg
Border Village	http://wiki.dominionstrategy.com/images/d/dd/Border_Village.jpg
Bridge	http://wiki.dominionstrategy.com/images/3/39/Bridge.jpg
Bureaucrat	http://wiki.dominionstrategy.com/images/4/4d/Bureaucrat.jpg
Butcher	http://wiki.dominionstrategy.com/images/e/ed/Butcher.jpg
Cache	http://wiki.dominionstrategy.com/images/6/66/Cache.jpg
Candlestick Maker	http://wiki.dominionstrategy.com/images/2/2c/Candlestick_Maker.jpg  
Caravan	http://wiki.dominionstrategy.com/images/c/c8/Caravan.jpg
Cartographer	http://wiki.dominionstrategy.com/images/d/d6/Cartographer.jpg
Catacombs	http://wiki.dominionstrategy.com/images/c/cd/Catacombs.jpg
Cellar	http://wiki.dominionstrategy.com/images/1/1c/Cellar.jpg
Chancellor	http://wiki.dominionstrategy.com/images/b/b7/Chancellor.jpg
Chapel	http://wiki.dominionstrategy.com/images/2/29/Chapel.jpg
City	http://wiki.dominionstrategy.com/images/3/30/City.jpg
Colony	http://wiki.dominionstrategy.com/images/6/60/Colony.jpg
Colony-new	http://wiki.dominionstrategy.com/images/b/be/Colony-new.jpg
Conspirator	http://wiki.dominionstrategy.com/images/4/42/Conspirator.jpg
Contraband	http://wiki.dominionstrategy.com/images/5/58/Contraband.jpg
Copper	http://wiki.dominionstrategy.com/images/f/fb/Copper.jpg
Coppersmith	http://wiki.dominionstrategy.com/images/4/40/Coppersmith.jpg
Council Room	http://wiki.dominionstrategy.com/images/e/e0/Council_Room.jpg
Count	http://wiki.dominionstrategy.com/images/a/a1/Count.jpg
Counterfeit	http://wiki.dominionstrategy.com/images/2/28/Counterfeit.jpg
Counting House	http://wiki.dominionstrategy.com/images/5/5d/Counting_House.jpg
Courtyard	http://wiki.dominionstrategy.com/images/3/30/Courtyard.jpg
Crossroads	http://wiki.dominionstrategy.com/images/c/cd/Crossroads.jpg
Cultist	http://wiki.dominionstrategy.com/images/1/18/Cultist.jpg
Curse	http://wiki.dominionstrategy.com/images/9/97/Curse.jpg
Curse-new	http://wiki.dominionstrategy.com/images/b/b9/Curse-new.jpg
Cutpurse	http://wiki.dominionstrategy.com/images/7/7d/Cutpurse.jpg
Dame Anna	http://wiki.dominionstrategy.com/images/a/ad/Dame_Anna.jpg
Dame Josephine	http://wiki.dominionstrategy.com/images/d/dd/Dame_Josephine.jpg
Dame Molly	http://wiki.dominionstrategy.com/images/1/10/Dame_Molly.jpg
Dame Natalie	http://wiki.dominionstrategy.com/images/8/85/Dame_Natalie.jpg
Dame Sylvia	http://wiki.dominionstrategy.com/images/c/c3/Dame_Sylvia.jpg
Death Cart	http://wiki.dominionstrategy.com/images/5/50/Death_Cart.jpg
Develop	http://wiki.dominionstrategy.com/images/f/f7/Develop.jpg
Diadem	http://wiki.dominionstrategy.com/images/3/35/Diadem.jpg
Doctor	http://wiki.dominionstrategy.com/images/b/b2/Doctor.jpg
Duchess	http://wiki.dominionstrategy.com/images/d/df/Duchess.jpg
Duchy	http://wiki.dominionstrategy.com/images/4/4a/Duchy.jpg
Duchy-new	http://wiki.dominionstrategy.com/images/5/54/Duchy-new.jpg
Duke	http://wiki.dominionstrategy.com/images/1/10/Duke.jpg
Embargo	http://wiki.dominionstrategy.com/images/f/fb/Embargo.jpg
Embassy	http://wiki.dominionstrategy.com/images/2/2f/Embassy.jpg
Envoy	http://wiki.dominionstrategy.com/images/0/0c/Envoy.jpg
Estate	http://wiki.dominionstrategy.com/images/9/91/Estate.jpg
Expand	http://wiki.dominionstrategy.com/images/d/dc/Expand.jpg
Explorer	http://wiki.dominionstrategy.com/images/3/3a/Explorer.jpg
Fairgrounds	http://wiki.dominionstrategy.com/images/7/7e/Fairgrounds.jpg
Familiar	http://wiki.dominionstrategy.com/images/4/48/Familiar.jpg
Farming Village	http://wiki.dominionstrategy.com/images/5/51/Farming_Village.jpg
Farmland	http://wiki.dominionstrategy.com/images/e/ea/Farmland.jpg
Feast	http://wiki.dominionstrategy.com/images/9/9c/Feast.jpg
Feodum	http://wiki.dominionstrategy.com/images/1/1f/Feodum.jpg
Festival	http://wiki.dominionstrategy.com/images/e/ec/Festival.jpg
Fishing Village	http://wiki.dominionstrategy.com/images/3/3b/Fishing_Village.jpg
Followers	http://wiki.dominionstrategy.com/images/1/12/Followers.jpg
Fool's Gold	http://wiki.dominionstrategy.com/images/e/ed/Fool's_Gold.jpg
Forager	http://wiki.dominionstrategy.com/images/e/e6/Forager.jpg
Forge	http://wiki.dominionstrategy.com/images/d/d7/Forge.jpg
Fortress	http://wiki.dominionstrategy.com/images/8/8a/Fortress.jpg
Fortune Teller	http://wiki.dominionstrategy.com/images/5/55/Fortune_Teller.jpg
Gardens	http://wiki.dominionstrategy.com/images/8/8c/Gardens.jpg
Ghost Ship	http://wiki.dominionstrategy.com/images/0/0a/Ghost_Ship.jpg
Gold	http://wiki.dominionstrategy.com/images/5/50/Gold.jpg
Golem	http://wiki.dominionstrategy.com/images/d/dc/Golem.jpg
Goons	http://wiki.dominionstrategy.com/images/e/e2/Goons.jpg
Governor	http://wiki.dominionstrategy.com/images/a/a2/Governor.jpg
Grand Market	http://wiki.dominionstrategy.com/images/8/81/Grand_Market.jpg
Graverobber	http://wiki.dominionstrategy.com/images/1/13/Graverobber.jpg
Great Hall	http://wiki.dominionstrategy.com/images/9/95/Great_Hall.jpg
Haggler	http://wiki.dominionstrategy.com/images/9/96/Haggler.jpg
Hamlet	http://wiki.dominionstrategy.com/images/d/df/Hamlet.jpg
Harem	http://wiki.dominionstrategy.com/images/9/9d/Harem.jpg
Harvest	http://wiki.dominionstrategy.com/images/1/1c/Harvest.jpg
Haven	http://wiki.dominionstrategy.com/images/c/c9/Haven.jpg
Herald	http://wiki.dominionstrategy.com/images/c/c1/Herald.jpg
Herbalist	http://wiki.dominionstrategy.com/images/2/26/Herbalist.jpg  
Hermit	http://wiki.dominionstrategy.com/images/8/8e/Hermit.jpg
Highway	http://wiki.dominionstrategy.com/images/2/29/Highway.jpg
Hoard	http://wiki.dominionstrategy.com/images/d/d1/Hoard.jpg
Horn of Plenty	http://wiki.dominionstrategy.com/images/2/20/Horn_of_Plenty.jpg
Horse Traders	http://wiki.dominionstrategy.com/images/c/c8/Horse_Traders.jpg
Hovel	http://wiki.dominionstrategy.com/images/f/f0/Hovel.jpg
Hunting Grounds	http://wiki.dominionstrategy.com/images/6/6a/Hunting_Grounds.jpg
Hunting Party	http://wiki.dominionstrategy.com/images/a/ab/Hunting_Party.jpg
Ill-Gotten Gains	http://wiki.dominionstrategy.com/images/9/91/Ill-Gotten_Gains.jpg
Inn	http://wiki.dominionstrategy.com/images/1/1f/Inn.jpg
Ironmonger	http://wiki.dominionstrategy.com/images/9/93/Ironmonger.jpg
Ironworks	http://wiki.dominionstrategy.com/images/7/76/Ironworks.jpg
Island	http://wiki.dominionstrategy.com/images/f/fd/Island.jpg
Jack of all Trades	http://wiki.dominionstrategy.com/images/3/38/Jack_of_all_Trades.jpg
Jester	http://wiki.dominionstrategy.com/images/1/1b/Jester.jpg
Journeyman	http://wiki.dominionstrategy.com/images/8/82/Journeyman.jpg
Junk Dealer	http://wiki.dominionstrategy.com/images/c/c2/Junk_Dealer.jpg
King's Court	http://wiki.dominionstrategy.com/images/8/8d/King's_Court.jpg
Laboratory	http://wiki.dominionstrategy.com/images/0/0c/Laboratory.jpg
Library	http://wiki.dominionstrategy.com/images/9/98/Library.jpg
Lighthouse	http://wiki.dominionstrategy.com/images/4/4f/Lighthouse.jpg
Loan	http://wiki.dominionstrategy.com/images/1/11/Loan.jpg
Lookout	http://wiki.dominionstrategy.com/images/c/c6/Lookout.jpg
Madman	http://wiki.dominionstrategy.com/images/1/19/Madman.jpg
Mandarin	http://wiki.dominionstrategy.com/images/6/68/Mandarin.jpg
Marauder	http://wiki.dominionstrategy.com/images/5/5e/Marauder.jpg
Margrave	http://wiki.dominionstrategy.com/images/0/06/Margrave.jpg
Market	http://wiki.dominionstrategy.com/images/7/7e/Market.jpg
Market Square	http://wiki.dominionstrategy.com/images/f/f1/Market_Square.jpg
Masquerade	http://wiki.dominionstrategy.com/images/0/0e/Masquerade.jpg
Masterpiece	http://wiki.dominionstrategy.com/images/0/09/Masterpiece.jpg
Menagerie	http://wiki.dominionstrategy.com/images/7/71/Menagerie.jpg
Mercenary	http://wiki.dominionstrategy.com/images/c/c5/Mercenary.jpg
Merchant Guild	http://wiki.dominionstrategy.com/images/a/af/Merchant_Guild.jpg
Merchant Ship	http://wiki.dominionstrategy.com/images/9/92/Merchant_Ship.jpg
Militia	http://wiki.dominionstrategy.com/images/a/a0/Militia.jpg
Mine	http://wiki.dominionstrategy.com/images/8/8e/Mine.jpg
Mining Village	http://wiki.dominionstrategy.com/images/7/7f/Mining_Village.jpg
Minion	http://wiki.dominionstrategy.com/images/4/47/Minion.jpg
Mint	http://wiki.dominionstrategy.com/images/b/bc/Mint.jpg
Moat	http://wiki.dominionstrategy.com/images/f/fe/Moat.jpg
Moneylender	http://wiki.dominionstrategy.com/images/7/70/Moneylender.jpg
Monument	http://wiki.dominionstrategy.com/images/a/ad/Monument.jpg
Mountebank	http://wiki.dominionstrategy.com/images/8/89/Mountebank.jpg
Mystic	http://wiki.dominionstrategy.com/images/3/37/Mystic.jpg
Native Village	http://wiki.dominionstrategy.com/images/6/67/Native_Village.jpg
Navigator	http://wiki.dominionstrategy.com/images/d/dd/Navigator.jpg
Necropolis	http://wiki.dominionstrategy.com/images/6/69/Necropolis.jpg
Noble Brigand	http://wiki.dominionstrategy.com/images/6/63/Noble_Brigand.jpg
Nobles	http://wiki.dominionstrategy.com/images/b/b6/Nobles.jpg
Nomad Camp	http://wiki.dominionstrategy.com/images/8/89/Nomad_Camp.jpg
Oasis	http://wiki.dominionstrategy.com/images/f/fc/Oasis.jpg
Oracle	http://wiki.dominionstrategy.com/images/9/97/Oracle.jpg
Outpost	http://wiki.dominionstrategy.com/images/b/b4/Outpost.jpg
Overgrown Estate	http://wiki.dominionstrategy.com/images/3/36/Overgrown_Estate.jpg   
Pawn	http://wiki.dominionstrategy.com/images/0/0f/Pawn.jpg
Pearl Diver	http://wiki.dominionstrategy.com/images/5/56/Pearl_Diver.jpg
Peddler	http://wiki.dominionstrategy.com/images/6/6f/Peddler.jpg
Philosopher's Stone	http://wiki.dominionstrategy.com/images/3/32/Philosopher's_Stone.jpg
Pillage	http://wiki.dominionstrategy.com/images/7/74/Pillage.jpg
Pirate Ship	http://wiki.dominionstrategy.com/images/4/42/Pirate_Ship.jpg
Platinum	http://wiki.dominionstrategy.com/images/7/72/Platinum.jpg
Platinum-new	http://wiki.dominionstrategy.com/images/4/42/Platinum-new.jpg
Plaza	http://wiki.dominionstrategy.com/images/f/fc/Plaza.jpg
Poor House	http://wiki.dominionstrategy.com/images/d/d6/Poor_House.jpg
Possession	http://wiki.dominionstrategy.com/images/3/3b/Possession.jpg
Potion	http://wiki.dominionstrategy.com/images/c/c3/Potion.jpg
Potion-new	http://wiki.dominionstrategy.com/images/6/67/Potion-new.jpg
Princess	http://wiki.dominionstrategy.com/images/4/42/Princess.jpg
Procession	http://wiki.dominionstrategy.com/images/7/7a/Procession.jpg
Province	http://wiki.dominionstrategy.com/images/8/81/Province.jpg
Quarry	http://wiki.dominionstrategy.com/images/6/65/Quarry.jpg
Rabble	http://wiki.dominionstrategy.com/images/f/f1/Rabble.jpg
Rats	http://wiki.dominionstrategy.com/images/7/70/Rats.jpg
Rebuild	http://wiki.dominionstrategy.com/images/f/f8/Rebuild.jpg
Remake	http://wiki.dominionstrategy.com/images/2/2b/Remake.jpg
Remodel	http://wiki.dominionstrategy.com/images/2/2e/Remodel.jpg
Rogue	http://wiki.dominionstrategy.com/images/f/f6/Rogue.jpg
Royal Seal	http://wiki.dominionstrategy.com/images/d/dd/Royal_Seal.jpg
Ruined Library	http://wiki.dominionstrategy.com/images/f/fe/Ruined_Library.jpg
Ruined Market	http://wiki.dominionstrategy.com/images/f/f2/Ruined_Market.jpg
Ruined Village	http://wiki.dominionstrategy.com/images/a/ae/Ruined_Village.jpg
Saboteur	http://wiki.dominionstrategy.com/images/6/60/Saboteur.jpg
Sage	http://wiki.dominionstrategy.com/images/7/70/Sage.jpg
Salvager	http://wiki.dominionstrategy.com/images/8/89/Salvager.jpg
Scavenger	http://wiki.dominionstrategy.com/images/d/d9/Scavenger.jpg
Scheme	http://wiki.dominionstrategy.com/images/8/8d/Scheme.jpg
Scout	http://wiki.dominionstrategy.com/images/4/46/Scout.jpg
Scrying Pool	http://wiki.dominionstrategy.com/images/7/79/Scrying_Pool.jpg
Sea Hag	http://wiki.dominionstrategy.com/images/8/8d/Sea_Hag.jpg
Secret Chamber	http://wiki.dominionstrategy.com/images/b/b3/Secret_Chamber.jpg
Shanty Town	http://wiki.dominionstrategy.com/images/8/8e/Shanty_Town.jpg
Silk Road	http://wiki.dominionstrategy.com/images/f/f6/Silk_Road.jpg
Silver	http://wiki.dominionstrategy.com/images/5/5d/Silver.jpg
Sir Bailey	http://wiki.dominionstrategy.com/images/a/a6/Sir_Bailey.jpg
Sir Destry	http://wiki.dominionstrategy.com/images/1/18/Sir_Destry.jpg
Sir Martin	http://wiki.dominionstrategy.com/images/a/ab/Sir_Martin.jpg
Sir Michael	http://wiki.dominionstrategy.com/images/2/21/Sir_Michael.jpg
Sir Vander	http://wiki.dominionstrategy.com/images/3/30/Sir_Vander.jpg
Smithy	http://wiki.dominionstrategy.com/images/3/36/Smithy.jpg
Smugglers	http://wiki.dominionstrategy.com/images/0/05/Smugglers.jpg
Soothsayer	http://wiki.dominionstrategy.com/images/0/01/Soothsayer.jpg
Spice Merchant	http://wiki.dominionstrategy.com/images/e/e2/Spice_Merchant.jpg
Spoils	http://wiki.dominionstrategy.com/images/9/9f/Spoils.jpg
Spy	http://wiki.dominionstrategy.com/images/c/cb/Spy.jpg
Squire	http://wiki.dominionstrategy.com/images/7/79/Squire.jpg
Stables	http://wiki.dominionstrategy.com/images/3/35/Stables.jpg
Stash	http://wiki.dominionstrategy.com/images/2/23/Stash.jpg
Steward	http://wiki.dominionstrategy.com/images/8/88/Steward.jpg
Stonemason	http://wiki.dominionstrategy.com/images/d/d2/Stonemason.jpg
Storeroom	http://wiki.dominionstrategy.com/images/b/b4/Storeroom.jpg
Survivors	http://wiki.dominionstrategy.com/images/7/7a/Survivors.jpg
Swindler	http://wiki.dominionstrategy.com/images/e/e7/Swindler.jpg
Tactician	http://wiki.dominionstrategy.com/images/e/ed/Tactician.jpg
Talisman	http://wiki.dominionstrategy.com/images/c/cf/Talisman.jpg
Taxman	http://wiki.dominionstrategy.com/images/e/e0/Taxman.jpg
Thief	http://wiki.dominionstrategy.com/images/f/f5/Thief.jpg
Throne Room	http://wiki.dominionstrategy.com/images/d/d1/Throne_Room.jpg
Torturer	http://wiki.dominionstrategy.com/images/a/a9/Torturer.jpg
Tournament	http://wiki.dominionstrategy.com/images/c/c4/Tournament.jpg
Trade Route	http://wiki.dominionstrategy.com/images/a/a7/Trade_Route.jpg
Trader	http://wiki.dominionstrategy.com/images/1/12/Trader.jpg
Trading Post	http://wiki.dominionstrategy.com/images/3/36/Trading_Post.jpg
Transmute	http://wiki.dominionstrategy.com/images/2/22/Transmute.jpg
Treasure Map	http://wiki.dominionstrategy.com/images/6/61/Treasure_Map.jpg
Treasury	http://wiki.dominionstrategy.com/images/f/fd/Treasury.jpg
Tribute	http://wiki.dominionstrategy.com/images/0/00/Tribute.jpg
Trusty Steed	http://wiki.dominionstrategy.com/images/1/12/Trusty_Steed.jpg
Tunnel	http://wiki.dominionstrategy.com/images/c/c2/Tunnel.jpg
University	http://wiki.dominionstrategy.com/images/9/9b/University.jpg
Upgrade	http://wiki.dominionstrategy.com/images/d/d3/Upgrade.jpg
Urchin	http://wiki.dominionstrategy.com/images/7/74/Urchin.jpg
Vagrant	http://wiki.dominionstrategy.com/images/3/3f/Vagrant.jpg
Vault	http://wiki.dominionstrategy.com/images/6/62/Vault.jpg
Venture	http://wiki.dominionstrategy.com/images/e/ef/Venture.jpg
Village	http://wiki.dominionstrategy.com/images/5/5a/Village.jpg
Vineyard	http://wiki.dominionstrategy.com/images/c/c8/Vineyard.jpg
Walled Village	http://wiki.dominionstrategy.com/images/6/6c/Walled_Village.jpg
Wandering Minstrel	http://wiki.dominionstrategy.com/images/f/f9/Wandering_Minstrel.jpg
Warehouse	http://wiki.dominionstrategy.com/images/6/6d/Warehouse.jpg
Watchtower	http://wiki.dominionstrategy.com/images/c/c2/Watchtower.jpg
Wharf	http://wiki.dominionstrategy.com/images/c/cc/Wharf.jpg
Wishing Well	http://wiki.dominionstrategy.com/images/f/f7/Wishing_Well.jpg
Witch	http://wiki.dominionstrategy.com/images/f/f3/Witch.jpg
Woodcutter	http://wiki.dominionstrategy.com/images/d/d6/Woodcutter.jpg
Worker's Village	http://wiki.dominionstrategy.com/images/1/12/Worker's_Village.jpg
Workshop	http://wiki.dominionstrategy.com/images/5/50/Workshop.jpg
Young Witch	http://wiki.dominionstrategy.com/images/9/9e/Young_Witch.jpg
\.


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: ts_system; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY ts_system (name, mu0, sigma0, beta, tau, draw_prob, sigma_reversion) FROM stdin;
Old Isotropish	25	25	25	0.25	0.0500000000000000028	0
AIsotropish	25	8.33333333333333393	4.16666666666666696	0.0833333333333333287	0.0500000000000000028	0
Isotropish	25	8.33333333333333393	4.16666666666666696	0.0833333333333333287	0.0500000000000000028	0.0100000000000000002
\.


--
-- PostgreSQL database dump complete
--

