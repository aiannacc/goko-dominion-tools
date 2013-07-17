#!/usr/bin/bash

pg_dump goko -s -x > schema.sql
