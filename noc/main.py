from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/about")
def about():
    return {"project": "NOC", "version": 1}