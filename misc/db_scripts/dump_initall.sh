#!/usr/bin/bash

pg_dump goko -s -x > misc/db_initdata/initdata-schema_and_all.sql
pg_dump -a -t advbot goko >> misc/db_initdata/initdata-schema_and_all.sql
pg_dump -a -t bot goko >> misc/db_initdata/initdata-schema_and_all.sql
pg_dump -a -t card_url goko >> misc/db_initdata/initdata-schema_and_all.sql
pg_dump -a -t ts_system goko >> misc/db_initdata/initdata-schema_and_all.sql
