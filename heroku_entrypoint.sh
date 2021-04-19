#!/bin/bash

DATABASE_URL="${DATABASE_URL//postgres:\/\//postgresql+asyncpg:\/\/}"

export DATABASE_URL="$DATABASE_URL"

export LD_LIBRARY_PATH="/usr/local/lib"


echo "================================"
echo "LD Library path: $LD_LIBRARY_PATH"
echo "Directory: $(pwd)"
echo "Libraries: $(ls /usr/local/lib)"
echo "================================"

bash run.sh
