#!/usr/bin/bash

pg_dump -a -t advbot goko > misc/db_initdata/initdata-advbots.sql
pg_dump -a -t bot goko > misc/db_initdata/initdata-bots.sql
pg_dump -a -t card_url goko > misc/db_initdata/initdata-card_url.sql
pg_dump -a -t ts_system goko > misc/db_initdata/initdata-ts_system.sql
