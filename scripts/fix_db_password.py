#!/usr/bin/env python3
"""Fix PostgreSQL password in .env on VPS and recreate container."""
from __future__ import annotations

import sys
import os

def main() -> None:
    try:
        import paramiko
    except ImportError:
        sys.exit("pip install paramiko")

    host, user, password = "147.45.243.199", "root", "tef-7#2v#auLP2"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    results = []

    def run(cmd: str, timeout: int = 120) -> tuple[str, str, int]:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        results.append((cmd, out, err, code))
        return out, err, code

    try:
        client.connect(host, username=user, password=password, timeout=15)
    except Exception as e:
        with open("reports/DB_PASSWORD_FIX_REPORT.md", "w", encoding="utf-8") as f:
            f.write("# DB PASSWORD FIX REPORT\n\n- **Подключение:** не удалось — " + str(e) + "\n")
        sys.exit(1)

    try:
        run("docker exec shop-bot-db-1 psql -U shopbot -c \"CREATE DATABASE leadfunnelbot;\" 2>/dev/null || echo 'DB already exists'")
        run("sed -i 's|shopbot:shopbot@|shopbot:shopbot_secret@|' /root/LeadFunnelBot/.env")
        run("sed -i 's|shopbot:shopbot_secret_secret@|shopbot:shopbot_secret@|' /root/LeadFunnelBot/.env")
        run("grep DATABASE_URL /root/LeadFunnelBot/.env")
        run("cd /root/LeadFunnelBot && docker compose -f docker-compose.prod.yml up -d --force-recreate")
        run("sleep 15")
        run("docker logs leadfunnelbot --tail 30 2>&1")
    finally:
        client.close()

    db_url_out = ""
    for cmd, out, err, _ in results:
        if "grep DATABASE_URL" in cmd:
            db_url_out = (out or err).strip()
            break
    logs_out = ""
    for cmd, out, err, _ in results:
        if "docker logs leadfunnelbot" in cmd:
            logs_out = (out or err).strip()
            break

    expected = "postgresql+asyncpg://shopbot:shopbot_secret@shop-bot-db-1:5432/leadfunnelbot"
    url_ok = expected in db_url_out or "shopbot_secret@" in db_url_out
    has_start = "Starting LeadFunnelBot" in logs_out
    has_conn = "Connecting database" in logs_out
    has_sched = "Starting scheduler" in logs_out
    has_bot = "Bot started" in logs_out
    up_exit = 1
    for cmd, _, _, code in results:
        if "up -d --force-recreate" in cmd:
            up_exit = code
            break

    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "DB_PASSWORD_FIX_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# DB PASSWORD FIX REPORT\n\n")
        f.write("- **Подключение через Paramiko:** да\n")
        f.write(f"- **Исправленный DATABASE_URL:** `{db_url_out or '(не получено)'}`\n")
        f.write(f"- **Запустился ли контейнер (up -d --force-recreate):** {'да' if up_exit == 0 else 'нет (exit ' + str(up_exit) + ')'}\n")
        f.write(f"- **Строки в логах (Starting LeadFunnelBot, Connecting database, Starting scheduler, Bot started):** "
                f"Start={has_start}, Conn={has_conn}, Sched={has_sched}, Bot={has_bot}\n")
        f.write(f"- **Появились ли строки 'Bot started':** {'да' if has_bot else 'нет'}\n\n")
        f.write("## Логи (последние 30 строк)\n\n```\n")
        f.write(logs_out.replace("```", "`"))
        f.write("\n```\n")
    print("Report written to", report_path)
    print("DATABASE_URL ok:", url_ok, "Bot started:", has_bot)


if __name__ == "__main__":
    main()
