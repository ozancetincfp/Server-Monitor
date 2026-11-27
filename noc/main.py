import os
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

load_dotenv()

API_KEY = os.environ.get("API_KEY", "")


DB_PATH = os.environ.get("DB_PATH", "noc.db")
WARNING_PERCENT = int(os.environ.get("WARNING_PERCENT", "80"))
CRITICAL_PERCENT = int(os.environ.get("CRITICAL_PERCENT", "90"))
OFFLINE_HOURS = int(os.environ.get("OFFLINE_HOURS", "2"))

app = FastAPI()


class Disk(BaseModel):
    mount: str
    size_kb: int
    used_kb: int
    avail_kb: int
    use_percent: int


class Report(BaseModel):
    disks: list[Disk]
    hostname: str


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS disk_usage (id INTEGER PRIMARY KEY, hostname TEXT, received_at TEXT, mount TEXT, size_kb INTEGER, used_kb INTEGER, avail_kb INTEGER, use_percent INTEGER)"
    )
    conn.commit()
    conn.close()


def disk_status(use_percent: int):
    if use_percent >= CRITICAL_PERCENT:
        return "CRITICAL"
    elif use_percent >= WARNING_PERCENT:
        return "WARNING"
    else:
        return "OK"


init_db()


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/about")
def about():
    return {"project": "NOC", "version": 1}


@app.post("/api/reports")
def receive_report(report: Report, x_api_key: str = Header(default="")):
    if not API_KEY or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    received_at = datetime.now(UTC).isoformat()
    conn = sqlite3.connect(DB_PATH)
    for disk in report.disks:
        conn.execute(
            "INSERT INTO disk_usage (hostname, received_at, mount, size_kb, used_kb, avail_kb, use_percent) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                report.hostname,
                received_at,
                disk.mount,
                disk.size_kb,
                disk.used_kb,
                disk.avail_kb,
                disk.use_percent,
            ),
        )
    conn.commit()
    conn.close()

    return {"received": True, "disk_count": len(report.disks)}


@app.get("/api/servers")
def list_servers():
    conn = sqlite3.connect(DB_PATH)
    servers = conn.execute(
        "SELECT hostname, MAX(received_at) FROM disk_usage GROUP BY hostname"
    ).fetchall()

    result = []
    for hostname, last_seen in servers:
        rows = conn.execute(
            "SELECT mount, use_percent FROM disk_usage WHERE hostname = ? AND received_at = ?",
            (hostname, last_seen),
        ).fetchall()

        disks = []
        statuses = []
        for mount, use_percent in rows:
            status = disk_status(use_percent)
            statuses.append(status)
            disks.append({"mount": mount, "use_percent": use_percent, "status": status})

        seen_at = datetime.fromisoformat(last_seen)
        offline_limit = datetime.now(UTC) - timedelta(hours=OFFLINE_HOURS)

        if seen_at < offline_limit:
            server_status = "OFFLINE"
        elif "CRITICAL" in statuses:
            server_status = "CRITICAL"
        elif "WARNING" in statuses:
            server_status = "WARNING"
        else:
            server_status = "OK"

        result.append(
            {
                "hostname": hostname,
                "last_seen": last_seen,
                "status": server_status,
                "disks": disks,
            }
        )

    conn.close()
    return result


@app.get("/api/servers/{hostname}")
def server_history(hostname: str):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT received_at, mount, use_percent FROM disk_usage WHERE hostname = ? ORDER BY received_at DESC LIMIT 100",
        (hostname,),
    ).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="Server not found")

    history = []
    for received_at, mount, use_percent in rows:
        history.append(
            {"received_at": received_at, "mount": mount, "use_percent": use_percent}
        )

    return history
