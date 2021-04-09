#!/bin/bash

psql -c "CREATE DATABASE minimaid;" "$DATABASE_URL"

DATABASE_URL="${DATABASE_URL//postgres:\/\//postgresql+asyncpg:\/\/}"

export DATABASE_URL="$DATABASE_URL"

echo "$DATABASE_URL"

python main.py
