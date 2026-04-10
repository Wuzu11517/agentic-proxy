import uvicorn
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from pipeline import run_pipeline
from modules.logger import get_stats, get_sessions
from modules.dashboard import get_dashboard_html
from modules.cache import clear_all
from proxy import ProxyError
from typing import Optional

app = FastAPI(title="agentic-proxy")


@app.post("/v1/messages")
async def messages(request: Request):
    try:
        body = await request.json()
        headers = dict(request.headers)
        is_streaming = body.get("stream", False)
        result = await run_pipeline(body, headers)

        if is_streaming:
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )

        return JSONResponse(content=result)

    except ProxyError as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/stats")
async def stats(session: Optional[str] = Query(default=None)):
    return JSONResponse(content=get_stats(session_id=session))


@app.get("/sessions")
async def sessions():
    return JSONResponse(content=get_sessions())


@app.post("/cache/clear")
async def clear_cache():
    clear_all()
    return JSONResponse(content={"status": "ok"})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=get_dashboard_html())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)