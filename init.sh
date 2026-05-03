#!/bin/bash

# Initialization script for Docker Postgres
#   1. Creates new user with username PG_USER and password PG_PASSWORD as
#      specified in .env
#   2. Creates new database with name PG_DBNAME using newly created user
#   3. Restores oscy data from data/db.dump into this database

set -e

psql --variable ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER $PG_USER WITH PASSWORD '$PG_PASSWORD' CREATEDB;
EOSQL

set PGPASSWORD=$PG_PASSWORD

createdb --username "$PG_USER" "$PG_DBNAME"

pg_restore --no-owner --single-transaction --username "$PG_USER" --dbname "$PG_DBNAME" ./data/db.dump
