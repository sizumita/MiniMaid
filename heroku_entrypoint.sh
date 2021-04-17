#!/bin/bash

DATABASE_URL="${DATABASE_URL//postgres:\/\//postgresql+asyncpg:\/\/}"

export DATABASE_URL="$DATABASE_URL"

export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib"


echo "================================"
echo "Database URL: $DATABASE_URL"
echo "LD Library path: $LD_LIBRARY_PATH"
echo "Directory: $(pwd)"
ls
echo "================================"

bash run.sh
