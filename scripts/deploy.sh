#!/bin/bash
# Production deploy: pull, build, up, migrations
set -e
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
