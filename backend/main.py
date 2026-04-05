from fastapi import FastAPI

app = FastAPI(title="Pipeline Debugger")


@app.get("/health")
async def health():
    return {"status": "ok"}
