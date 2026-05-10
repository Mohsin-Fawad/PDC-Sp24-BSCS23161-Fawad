import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from breaker import LLMBreaker, BreakerState

StudentID  = "BSCS23161"
LlmUrl     = "http://127.0.0.1:8001/generate"
LlmTimeout = 10.0

App     = FastAPI(title="StudySync API")
Breaker = LLMBreaker(maxFails=3, cooldown=10.0)


@App.middleware("http")
async def AttachStudentHeader(Req: Request, NextCall):
    Res = await NextCall(Req)
    Res.headers["X-Student-ID"] = StudentID
    return Res


@App.get("/health")
async def HealthCheck():
    return {"status": "ok", "studentId": StudentID}


@App.get("/breaker-status")
async def BreakerStatus():
    return Breaker.FetchStatus()


@App.post("/breaker-reset")
async def BreakerReset():
    Breaker.DoReset()
    return {"message": "reset done", "state": Breaker.State.value}


@App.get("/raw-summary")
async def RawSummary(Prompt: str = "summarize"):
    try:
        async with httpx.AsyncClient(timeout=65.0) as C:
            Resp = await C.post(LlmUrl, json={"prompt": Prompt})
        return {"source": "llm", "summary": Resp.json().get("result")}
    except Exception as E:
        return JSONResponse(status_code=503, content={"error": str(E)})


@App.get("/generate-summary")
async def GenerateSummary(Prompt: str = "summarize"):

    if not Breaker.CanProceed():
        return JSONResponse(status_code=503, content={
            "source":  "fallback",
            "state":   Breaker.State.value,
            "summary": None,
            "message": "AI service temporarily down. Try again in a few minutes.",
        })

    try:
        async with httpx.AsyncClient(timeout=LlmTimeout) as C:
            Resp = await C.post(LlmUrl, json={"prompt": Prompt})

        if Resp.status_code >= 500:
            raise Exception(f"LLM returned {Resp.status_code}")

        Breaker.LogSuccess()
        return {
            "source":  "llm",
            "state":   Breaker.State.value,
            "summary": Resp.json().get("result"),
            "message": None,
        }

    except httpx.TimeoutException:
        Breaker.LogFailure()
        return JSONResponse(status_code=503, content={
            "source":  "fallback",
            "state":   Breaker.State.value,
            "summary": None,
            "message": "AI service timed out.",
        })

    except Exception as E:
        Breaker.LogFailure()
        return JSONResponse(status_code=503, content={
            "source":  "fallback",
            "state":   Breaker.State.value,
            "summary": None,
            "message": "AI service unavailable.",
        })


if __name__ == "__main__":
    uvicorn.run(App, host="127.0.0.1", port=8000)
