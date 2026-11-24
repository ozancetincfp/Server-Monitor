import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

DB_PATH = "noc.db"

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
    return latest_reports