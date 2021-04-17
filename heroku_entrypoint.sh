#!/bin/bash

DATABASE_URL="${DATABASE_URL//postgres:\/\//postgresql+asyncpg:\/\/}"

export DATABASE_URL="$DATABASE_URL"

echo "$DATABASE_URL"

bash run.sh
