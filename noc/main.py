from fastapi import FastAPI
from pydantic import BaseModel
from starlette.routing import Host

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


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/about")
def about():
    return {"project": "NOC", "version": 1}


@app.post("/api/reports")
def receive_report(report: Report):
    print(report)
    return {"received": True, "disk_count": len(report.disks)}