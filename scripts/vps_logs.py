#!/usr/bin/env python3
"""Fetch last 40 lines of leadfunnelbot logs from VPS."""
from __future__ import annotations

import sys
try:
    import paramiko
except ImportError:
    sys.exit("pip install paramiko")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("147.45.243.199", username="root", password="tef-7#2v#auLP2", timeout=15)
stdin, stdout, stderr = client.exec_command("docker logs leadfunnelbot --tail 40 2>&1", timeout=10)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
client.close()
print(out or err)
