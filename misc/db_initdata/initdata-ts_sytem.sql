--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

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
-- Data for Name: ts_system; Type: TABLE DATA; Schema: public; Owner: ai
--

COPY ts_system (name, mu0, sigma0, beta, tau, draw_prob, sigma_reversion) FROM stdin;
Old Isotropish	25	25	25	0.25	0.0500000000000000028	0
AIsotropish	25	8.33333333333333393	4.16666666666666696	0.0833333333333333287	0.0500000000000000028	0
Isotropish	25	8.33333333333333393	4.16666666666666696	0.0833333333333333287	0.0500000000000000028	0.0100000000000000002
\.


--
-- Name: ts_system_pkey; Type: CONSTRAINT; Schema: public; Owner: ai; Tablespace: 
--

ALTER TABLE ONLY ts_system
    ADD CONSTRAINT ts_system_pkey PRIMARY KEY (name);


--
-- Name: ts_system; Type: ACL; Schema: public; Owner: ai
--

REVOKE ALL ON TABLE ts_system FROM PUBLIC;
REVOKE ALL ON TABLE ts_system FROM ai;
GRANT ALL ON TABLE ts_system TO ai;
GRANT SELECT ON TABLE ts_system TO forum;


--
-- PostgreSQL database dump complete
--

