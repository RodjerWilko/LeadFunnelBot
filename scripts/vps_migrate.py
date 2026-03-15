#!/usr/bin/env python3
"""Run alembic upgrade head on VPS."""
from __future__ import annotations

import sys
try:
    import paramiko
except ImportError:
    sys.exit("pip install paramiko")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("147.45.243.199", username="root", password="tef-7#2v#auLP2", timeout=15)
# Stamp 001 if tables exist but version table empty, then upgrade to head
stdin, stdout, stderr = client.exec_command(
    "cd /root/LeadFunnelBot && docker compose -f docker-compose.prod.yml run --rm bot sh -c "
    "'alembic stamp 001_initial 2>/dev/null; alembic upgrade head' 2>&1",
    timeout=90,
)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
code = stdout.channel.recv_exit_status()
client.close()
print("exit", code)
print(out or err)
