--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: game_result; Type: TABLE; Schema: public; Owner: ai; Tablespace: 
--

CREATE TABLE game_result (
    "time" timestamp without time zone,
    logfile character(50) NOT NULL,
    pcount integer NOT NULL,
    guest boolean NOT NULL,
    bot boolean NOT NULL,
    min_turns integer NOT NULL,
    rank1 integer NOT NULL,
    rank2 integer NOT NULL,
    rank3 integer,
    rank4 integer,
    rank5 integer,
    rank6 integer,
    pname1 character varying(50) NOT NULL,
    pname2 character varying(50) NOT NULL,
    pname3 character varying(50),
    pname4 character varying(50),
    pname5 character varying(50),
    pname6 character varying(50)
);


ALTER TABLE public.game_result OWNER TO ai;

ALTER TABLE public.game_result ADD PRIMARY KEY (logfile);

--
-- Name: gr_bot; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gr__bot ON game_result USING btree (bot);


--
-- Name: gr_guest; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gr__guest ON game_result USING btree (guest);


--
-- Name: gr_pcount; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gr__pcount ON game_result USING btree (pcount);


--
-- Name: gr_time; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gr__time ON game_result USING btree ("time");


--
-- Name: gr_turns; Type: INDEX; Schema: public; Owner: ai; Tablespace: 
--

CREATE INDEX gr__turns ON game_result USING btree (min_turns);


--
-- PostgreSQL database dump complete
--

