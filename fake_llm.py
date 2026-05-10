import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException

FakeLLM = FastAPI()
Mode    = {"current": "normal"}


@FakeLLM.get("/health")
async def FakeLLMHealth():
    return {"status": "ok", "mode": Mode["current"]}


@FakeLLM.post("/mode/{Val}")
async def SetMode(Val: str):
    Mode["current"] = Val
    return {"mode": Val}


@FakeLLM.post("/generate")
async def Generate(Body: dict):
    match Mode["current"]:
        case "slow":
            await asyncio.sleep(60)
            return {"result": "slow reply"}
        case "error":
            raise HTTPException(status_code=500, detail="LLM crashed")
        case _:
            await asyncio.sleep(0.2)
            return {"result": f"Summary of: {Body.get('prompt', 'your text')}"}


if __name__ == "__main__":
    uvicorn.run(FakeLLM, host="127.0.0.1", port=8001)
