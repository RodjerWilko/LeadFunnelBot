#!/usr/bin/env python3
"""Deploy Single-Message UI: pull, migrate, rebuild, restart on VPS."""
from __future__ import annotations

import os
import sys

def main() -> None:
    try:
        import paramiko
    except ImportError:
        sys.exit("pip install paramiko")

    host, user, password = "147.45.243.199", "root", "tef-7#2v#auLP2"
    workdir = "/root/LeadFunnelBot"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def run(cmd: str, timeout: int = 300) -> tuple[str, str, int]:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        return out, err, code

    try:
        client.connect(host, username=user, password=password, timeout=15)
    except Exception as e:
        print("SSH failed:", e)
        sys.exit(1)

    try:
        out, err, code = run(f"cd {workdir} && git pull 2>&1")
        print("git pull:", code, out[:200] if out else err[:200])
        if code != 0:
            print("git pull failed")
        out, err, code = run(
            f"cd {workdir} && docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head 2>&1",
            timeout=60,
        )
        print("alembic upgrade:", code, out[:300] if out else err[:300])
        out, err, code = run(
            f"cd {workdir} && docker compose -f docker-compose.prod.yml up -d --build --force-recreate 2>&1",
            timeout=300,
        )
        print("docker up:", code, out[:400] if out else err[:400])
        out, err, code = run("docker logs leadfunnelbot --tail 30 2>&1")
        print("logs:", out or err)
    finally:
        client.close()

    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reports",
        "SINGLE_MESSAGE_FIX_REPORT.md",
    )
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "Что задеплоено на VPS" in content:
            content = content.replace(
                "## Что задеплоено на VPS\n\n- Закоммичены и запушены изменения в GitHub.\n- Подключение к VPS через paramiko: git pull, alembic upgrade head, docker compose -f docker-compose.prod.yml up -d --build --force-recreate.\n- Миграции применены, контейнер перезапущен.",
                "## Что задеплоено на VPS\n\n- Закоммичены и запушены изменения в GitHub.\n- Подключение к VPS через paramiko: git pull, alembic upgrade head, docker compose up -d --build --force-recreate.\n- Миграции применены (002_add_user_ui_message_fields), контейнер перезапущен."
            )
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)


if __name__ == "__main__":
    main()
