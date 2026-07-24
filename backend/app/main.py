from fastapi import FastAPI

app = FastAPI(title="VPN SaaS")

@app.get("/")
def root():
    return {"status": "ok"}