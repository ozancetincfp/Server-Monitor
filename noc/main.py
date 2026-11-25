import sqlite3
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from pydantic import BaseModel

DB_PATH = "noc.db"
WARNING_PERCENT = 80
CRITICAL_PERCENT = 90
OFFLINE_HOURS = 2

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
    conn.execute("CREATE TABLE IF NOT EXISTS disk_usage (id INTEGER PRIMARY KEY, hostname TEXT, received_at TEXT, mount TEXT, size_kb INTEGER, used_kb INTEGER, avail_kb INTEGER, use_percent INTEGER)")
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



latest_reports = {}


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/about")
def about():
    return {"project": "NOC", "version": 1}


@app.post("/api/reports")
def receive_report(report: Report):
    latest_reports[report.hostname] = report

    received_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    for disk in report.disks:
        conn.execute(
            "INSERT INTO disk_usage (hostname, received_at, mount, size_kb, used_kb, avail_kb, use_percent) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (report.hostname,received_at ,disk.mount, disk.size_kb, disk.used_kb, disk.avail_kb, disk.use_percent),
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
        offline_limit = datetime.now(timezone.utc) - timedelta(hours=OFFLINE_HOURS)

        if seen_at < offline_limit:                                                    
            server_status = "OFFLINE"
        elif "CRITICAL" in statuses:
            server_status = "CRITICAL"
        elif "WARNING" in statuses:
            server_status = "WARNING"
        else:
            server_status = "OK"

        result.append({
            "hostname": hostname,
            "last_seen": last_seen,
            "status": server_status,
            "disks": disks,
        })

    conn.close()
    return result