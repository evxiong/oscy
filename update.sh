#!/bin/bash

# Interactive update script (for local use)
#   1. Runs Python database update script
#   2. Updates `README.md`
#   3. Creates new `data/db.dump`
#   4. Creates new `data/oscars.csv`
#   5. Updates production cloud database
#   6. Revalidates production Next.js cache
# 
# Usage:
#   ./update.sh <stage> <edition>
#
#   <stage> is one of `nominations`, `unofficial`, `official`
#   <edition> is the Oscars ceremony edition to update
#
#   Example:
#       ./update.sh nominations 98
#
#   Data updates should happen annually in 3 stages:
#       1. Nominations (mid January) - after Academy releases nominations
#       2. Unofficial results (day after ceremony) - after results are posted to
#          IMDb
#       3. Official results (month after ceremony) - after results are posted to
#          official Academy database
# 
#   If any stage is missed, run the missed stage(s) prior to running the current
#   stage.
#
# Prerequisites:
#   - This script assumes the presence of a `PGPASSWORD` env var or
#     `.pgpass`/`pgpass.conf` password file. See
#     https://www.postgresql.org/docs/current/libpq-pgpass.html for details.
#   - In `.env`, `PG_USER` and `PG_DBNAME` should be set to local database;
#     `PG_PROD_URI` should be set to cloud production database (owner, no
#     connection pooling)

set -e

# Validate args
if [[ $# -ne 2 || ! "$1" =~ ^(nominations|unofficial|official)$ || ! "$2" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <stage> <edition>" >&2
    echo >&2
    echo '<stage> is one of `nominations`, `unofficial`, `official`' >&2
    echo '<edition> is the Oscars ceremony edition to update' >&2
    exit 1
fi

stage="$1"
edition="$2"

# Load env vars from .env
set -a
source .env
set +a

# 1. Run interactive Python database update script
cd backend
source .venv/Scripts/activate

cd db
python -m src.oscy.update "$stage" "$edition"
cd ../..

echo 'Updated db'

# 2. Update `README.md` with update date
ordinal() {
    local n=$1
    local last_two=$((n % 100))
    local last_one=$((n % 10))

    if (( last_two >= 11 && last_two <= 13 )); then
        echo "${n}th"
    else
        case $last_one in
            1) echo "${n}st" ;;
            2) echo "${n}nd" ;;
            3) echo "${n}rd" ;;
            *) echo "${n}th" ;;
        esac
    fi
}

edition_ordinal=$(ordinal "$edition")
current_date=$(date +"%b. %-d, %Y")

if [[ "$stage" == "nominations" ]]; then
    stage_output="nominations"
else
    stage_output="results"
fi

sed -bi "s/\*\*Data last updated.*\*\*/**Data last updated ${current_date} (includes ${edition_ordinal} Oscars ${stage_output})**/" README.md

echo 'Updated README.md'

# 3. Create new SQL dump at `data/db.dump`
pg_dump -Fc -U "$PG_USER" -d "$PG_DBNAME" > data/db.dump

echo 'Created new SQL dump at `data/db.dump`'

# 4. Create new `data/oscars.csv` export
cd backend/db
python -m src.oscy.export

echo 'Created new CSV export at `data/oscars.csv`'

# 5. Update cloud database
cd ../../data
psql --variable ON_ERROR_STOP=1 --dbname "$PG_PROD_URI" <<-EOSQL
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
EOSQL

pg_restore --no-owner --single-transaction --dbname "$PG_PROD_URI" db.dump

psql --variable ON_ERROR_STOP=1 --dbname "$PG_PROD_URI" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO oscy_ro;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO oscy_ro;
EOSQL

echo 'Updated production db'

# 6. Revalidate version cache tag in production Next.js
cd ../backend/db
python -m src.oscy.revalidate version

echo 'Revalidated production Next.js cache'
