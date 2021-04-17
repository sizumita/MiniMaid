#!/bin/bash

DATABASE_URL="${DATABASE_URL//postgres:\/\//postgresql+asyncpg:\/\/}"

export DATABASE_URL="$DATABASE_URL"

export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib"

echo "$DATABASE_URL"

bash run.sh
