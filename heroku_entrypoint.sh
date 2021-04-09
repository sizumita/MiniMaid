#!/bin/bash

psql -c "CREATE DATABASE minimaid;" "$DATABASE_URL"

DATABASE_URL=$(sed -e 's_postgres://_postgresql+asyncpg://_' "$DATABASE_URL")
# shellcheck disable=SC2016
DATABASE_URL=$(sed -e 's_$_/minimaid_' "$DATABASE_URL")

export DATABASE_URL="$DATABASE_URL"

python main.py
