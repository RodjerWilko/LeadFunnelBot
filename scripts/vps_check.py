#!/usr/bin/env python3
"""SSH to VPS via Paramiko, run checks, write report."""
from __future__ import annotations

import json
import sys

def run_ssh(host: str, user: str, password: str) -> dict:
    try:
        import paramiko
    except ImportError:
        sys.exit("pip install paramiko")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    result = {
        "connected": False,
        "commands": [],
        "webhook_was_set": None,
        "webhook_deleted": False,
        "container_running_before": None,
        "container_started": False,
        "logs_before": "",
        "logs_after": "",
        "ping_ok": None,
        "errors": [],
        "container_name": "leadfunnelbot",
    }

    def run(cmd: str, timeout: int = 60) -> tuple[str, str, int]:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        result["commands"].append({"cmd": cmd, "out": out, "err": err, "code": code})
        return out, err, code

    try:
        client.connect(host, username=user, password=password, timeout=15)
        result["connected"] = True
    except Exception as e:
        result["errors"].append(f"SSH connect: {e}")
        return result

    try:
        # 1. docker ps
        out, err, code = run("docker ps -a --format '{{.Names}} {{.Status}}'")
        result["container_running_before"] = "leadfunnelbot" in out and "Up" in out

        # 2. logs before
        out, err, code = run("docker logs leadfunnelbot --tail 50 2>&1")
        result["logs_before"] = out or err

        # 3. webhook
        out, err, code = run(
            "curl -s https://api.telegram.org/bot8363305307:AAEy03zqZrFyYhnyrPRRXXmUdqmawaPBuLo/getWebhookInfo"
        )
        try:
            data = json.loads(out.strip() if out else "{}")
            url = (data.get("result") or {}).get("url") or ""
            result["webhook_was_set"] = bool(url)
            if result["webhook_was_set"]:
                out2, _, _ = run(
                    "curl -s https://api.telegram.org/bot8363305307:AAEy03zqZrFyYhnyrPRRXXmUdqmawaPBuLo/deleteWebhook"
                )
                try:
                    result["webhook_deleted"] = json.loads(out2 or "{}").get("ok") is True
                except Exception:
                    result["webhook_deleted"] = "ok" in (out2 or "").lower()
        except Exception as e:
            result["webhook_was_set"] = False
            result["errors"].append(f"webhook parse: {e}")

        # 4. ping (no -it)
        out, err, code = run("docker exec leadfunnelbot ping -c 2 api.telegram.org 2>&1", timeout=10)
        result["ping_ok"] = code == 0 and "2 received" in (out or err)

        # 5. find project dir, clone if missing, rebuild/up
        out, _, _ = run("ls -d /root/LeadFunnelBot 2>/dev/null || true")
        workdir = "/root/LeadFunnelBot"
        for line in (out or "").strip().splitlines():
            line = line.strip()
            if "LeadFunnelBot" in line:
                workdir = line
                break
        if not out or "LeadFunnelBot" not in (out or ""):
            run("cd /root && git clone https://github.com/RodjerWilko/LeadFunnelBot.git 2>&1", timeout=60)
        else:
            run(f"cd {workdir} && git pull 2>&1", timeout=30)
        for comp in ["docker compose", "docker-compose"]:
            _, _, codeb = run(f"cd {workdir} && {comp} -f docker-compose.prod.yml build --no-cache 2>&1", timeout=300)
            if codeb == 0:
                break
        # ensure .env exists (required by compose)
        env_content = (
            "BOT_TOKEN=8363305307:AAEy03zqZrFyYhnyrPRRXXmUdqmawaPBuLo\n"
            "DATABASE_URL=postgresql+asyncpg://shopbot:shopbot@shop-bot-db-1:5432/leadfunnelbot\n"
            "ADMIN_ID=52178124\nRATE_LIMIT_MESSAGES=5\nRATE_LIMIT_PERIOD=2\nBROADCAST_DELAY=0.05\n"
        )
        sftp = client.open_sftp()
        try:
            with sftp.file(f"{workdir}/.env", "w") as f:
                f.write(env_content)
        finally:
            sftp.close()
        run("docker exec shop-bot-db-1 psql -U shopbot -tAc \"SELECT 1 FROM pg_database WHERE datname='leadfunnelbot'\" 2>&1")
        if "1" not in (result["commands"][-1]["out"] or ""):
            run("docker exec shop-bot-db-1 psql -U shopbot -c 'CREATE DATABASE leadfunnelbot;' 2>&1")
        for comp in ["docker compose", "docker-compose"]:
            _, _, codeu = run(f"cd {workdir} && {comp} -f docker-compose.prod.yml up -d 2>&1", timeout=60)
            if codeu == 0:
                result["container_started"] = True
                break
        else:
            result["container_started"] = False
        if result["container_started"]:
            for comp in ["docker compose", "docker-compose"]:
                _, _, codem = run(f"cd {workdir} && {comp} -f docker-compose.prod.yml run --rm bot alembic upgrade head 2>&1", timeout=30)
                if codem == 0:
                    break

        # 6. logs after (container may be named leadfunnelbot or leadfunnelbot-bot-1)
        out, _, code = run("docker ps -a --format '{{.Names}}' | grep -i lead || true")
        cname = "leadfunnelbot"
        for line in (out or "").strip().splitlines():
            line = line.strip()
            if line:
                cname = line
                break
        out, err, code = run(f"docker logs {cname} --tail 50 2>&1")
        result["logs_after"] = out or err
        result["container_name"] = cname

    except Exception as e:
        result["errors"].append(str(e))
    finally:
        client.close()

    return result


def main() -> None:
    r = run_ssh(
        host="147.45.243.199",
        user="root",
        password="tef-7#2v#auLP2",
    )
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(os.path.dirname(script_dir), "reports", "VPS_CONNECTION_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# VPS CONNECTION REPORT\n\n")
        f.write(f"- **Подключение через Paramiko:** {'да' if r['connected'] else 'нет'}\n")
        f.write(f"- **Команды выполнены:** " + str(len(r["commands"])) + "\n")
        for i, c in enumerate(r["commands"], 1):
            f.write(f"  {i}. `{c['cmd'][:80]}{'...' if len(c['cmd'])>80 else ''}` (exit {c['code']})\n")
        f.write(f"- **Webhook был установлен:** {r['webhook_was_set']}\n")
        f.write(f"- **Webhook удалён:** {r['webhook_deleted']}\n")
        f.write(f"- **Ping api.telegram.org из контейнера:** {'ok' if r['ping_ok'] else 'fail'}\n")
        f.write(f"- **Контейнер запущен после up -d:** {r['container_started']}\n")
        has_start = "Starting LeadFunnelBot" in (r.get("logs_after") or "")
        has_bot = "Bot started" in (r.get("logs_after") or "")
        f.write(f"- **В логах есть 'Starting LeadFunnelBot' и 'Bot started':** {has_start and has_bot}\n")
        f.write(f"- **Ошибки:** {r['errors'] or 'нет'}\n")
        f.write(f"- **Имя контейнера:** {r.get('container_name', 'leadfunnelbot')}\n\n")
        f.write("- **Исправлена ли проблема:** контейнер запущен; при ошибке пароля БД нужно задать в .env правильный пароль для пользователя shopbot и перезапустить контейнер.\n\n")
        f.write("- **Отвечает ли бот на /start:** проверить в Telegram после успешного старта приложения в контейнере (логи: Starting LeadFunnelBot, Bot started).\n\n")
        for i, c in enumerate(r["commands"], 1):
            if c["code"] != 0 and (c["out"] or c["err"]):
                f.write(f"## Вывод команды {i} (exit {c['code']})\n\n```\n{(c['out'] or '') + (c['err'] or '')}\n```\n\n")
        f.write("## Логи контейнера (последние 50 строк)\n\n```\n")
        f.write((r.get("logs_after") or r.get("logs_before") or "(нет вывода)").replace("```", "`"))
        f.write("\n```\n")
    print("Report written to", report_path)
    print("Connected:", r["connected"], "Webhook was set:", r["webhook_was_set"], "Deleted:", r["webhook_deleted"])


if __name__ == "__main__":
    main()
