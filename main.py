import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pipeline import run_pipeline
from logger import generate_report

app = FastAPI(title="agentic-proxy")


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    result = await run_pipeline(body, headers)
    return JSONResponse(content=result)


@app.on_event("shutdown")
async def shutdown():
    generate_report()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)