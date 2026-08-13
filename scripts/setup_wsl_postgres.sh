#!/usr/bin/env bash
# Provision Postgres 16 + pgvector inside WSL Ubuntu for the Team A backend.
# Use this when Docker Hub is unreachable and `docker compose up -d` can't pull.
#
# Run as root, from the repo root:
#   wsl -d Ubuntu-24.04 -u root -- bash "$(wslpath -a scripts/setup_wsl_postgres.sh)"
# or with an explicit path:
#   wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/path/to/repo/scripts/setup_wsl_postgres.sh
set -euo pipefail

# Resolve the repo root from this script's own location so the schema path
# works regardless of where the repo is checked out.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA="${REPO_ROOT}/sql/schema.sql"

PGVER=16
PGCONF="/etc/postgresql/${PGVER}/main/postgresql.conf"
PGHBA="/etc/postgresql/${PGVER}/main/pg_hba.conf"

echo "== configuring ${PGCONF} =="
ls -la "$PGCONF"
sed -i "s/^#\?listen_addresses.*/listen_addresses = '*'/" "$PGCONF"

echo "== configuring ${PGHBA} =="
if ! grep -q "0.0.0.0/0" "$PGHBA"; then
    echo "host    all             all             0.0.0.0/0               md5" >> "$PGHBA"
fi

echo "== starting cluster =="
pg_ctlcluster "$PGVER" main start || service postgresql start || true
for i in $(seq 1 20); do
    pg_isready -q && break
    sleep 1
done
pg_isready

echo "== creating role + database =="
su - postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='teama'\"" | grep -q 1 \
    || su - postgres -c "psql -c \"CREATE ROLE teama LOGIN PASSWORD 'teama' SUPERUSER\""

su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='team_a'\"" | grep -q 1 \
    || su - postgres -c "createdb -O teama team_a"

echo "== applying schema from ${SCHEMA} =="
test -f "$SCHEMA" || { echo "schema not found at $SCHEMA" >&2; exit 1; }
# `su - postgres` can't read a Windows-mounted path, so pipe it in on stdin.
su postgres -c "psql -d team_a" < "$SCHEMA" 2>&1 | tail -25

echo "== verifying =="
su - postgres -c "psql -d team_a -tAc \"SELECT extname FROM pg_extension WHERE extname='vector'\""
su - postgres -c "psql -d team_a -tAc \"SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename\""
pg_lsclusters
