#!/usr/bin/bash

pg_dump -t advbot goko > misc/db_initdata/initdata-advbots.sql
pg_dump -t bot goko > misc/db_initdata/initdata-bots.sql
pg_dump -t card_url goko > misc/db_initdata/initdata-card_url.sql
pg_dump -t ts_system goko > misc/db_initdata/initdata-ts_system.sql
