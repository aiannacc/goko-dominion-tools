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

