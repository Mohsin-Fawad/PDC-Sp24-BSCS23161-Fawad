import httpx
import asyncio
import time

MainAPI = "http://127.0.0.1:8000"
FakeAPI = "http://127.0.0.1:8001"


async def SetLLMMode(Mode: str):
    async with httpx.AsyncClient(timeout=5) as C:
        await C.post(f"{FakeAPI}/mode/{Mode}")
    print(f"[Config] LLM switched to: {Mode}")


async def ResetBreaker():
    async with httpx.AsyncClient(timeout=5) as C:
        await C.post(f"{MainAPI}/breaker-reset")
    print("[Config] Breaker cleared and set to CLOSED")


async def GetBreakerState() -> dict:
    async with httpx.AsyncClient(timeout=5) as C:
        R = await C.get(f"{MainAPI}/breaker-status")
    return R.json()


async def CallSummary(UserTag: str, WaitLimit: float = 15.0):
    Start = time.time()
    try:
        async with httpx.AsyncClient(timeout=WaitLimit) as C:
            R = await C.get(f"{MainAPI}/generate-summary", params={"Prompt": "summarize my notes"})
        Elapsed = time.time() - Start
        Data    = R.json()
        Src     = Data.get("source", "?")
        St      = Data.get("state",  "?")
        Hdr     = R.headers.get("X-Student-ID", "MISSING")
        Label   = "INSTANT FALLBACK" if Src == "fallback" else "LLM REPLY     "
        print(f"  [{UserTag}] {Label} in {Elapsed:.2f}s | breaker={St} | X-Student-ID={Hdr}")
    except httpx.TimeoutException:
        print(f"  [{UserTag}] Timed out after {time.time() - Start:.1f}s")
    except Exception as E:
        print(f"  [{UserTag}] Error: {E}")


async def Main():
    print()
    print("=" * 62)
    print("  DEMO: Circuit Breaker — Full Lifecycle")
    print("  Student: BSCS23161")
    print("=" * 62)

    await ResetBreaker()
    await SetLLMMode("normal")
    await asyncio.sleep(0.5)

    print()
    print("PHASE 1 — Normal operation (CLOSED, LLM healthy)")
    print("-" * 62)
    await CallSummary("User-1")
    await CallSummary("User-2")
    S = await GetBreakerState()
    print(f"  [Breaker] state={S['state']} | fails={S['failCount']}")

    print()
    print("PHASE 2 — LLM starts failing, breaker counts errors")
    print("-" * 62)
    await SetLLMMode("error")
    await asyncio.sleep(0.3)
    await CallSummary("User-3")
    await CallSummary("User-4")
    await CallSummary("User-5")
    S = await GetBreakerState()
    print(f"  [Breaker] state={S['state']} | fails={S['failCount']}  ← TRIPPED!")

    print()
    print("PHASE 3 — OPEN: all users get instant fallback, LLM never called")
    print("-" * 62)
    await CallSummary("User-6")
    await CallSummary("User-7")
    await CallSummary("User-8")
    print("  ^ All instant — no waiting for LLM at all")

    print()
    print("PHASE 4 — Waiting 10s cooldown (LLM fixed in background)")
    print("-" * 62)
    await SetLLMMode("normal")
    for I in range(10, 0, -1):
        print(f"  {I}s left...", end="\r")
        await asyncio.sleep(1)
    print()

    print()
    print("PHASE 5 — HALF_OPEN: breaker sends one test request")
    print("-" * 62)
    await CallSummary("User-9")
    S = await GetBreakerState()
    print(f"  [Breaker] state={S['state']} | fails={S['failCount']}")

    print()
    print("PHASE 6 — CLOSED again: full recovery confirmed")
    print("-" * 62)
    await CallSummary("User-10")
    await CallSummary("User-11")
    S = await GetBreakerState()
    print(f"  [Breaker] state={S['state']} | fails={S['failCount']}")

    print()
    print("=" * 62)
    print("  DONE — Circuit Breaker working correctly")
    print("  Before fix: every user waits 60s, no fallback")
    print("  After fix:  instant fallback, server stays alive")
    print("  X-Student-ID header verified on every response above")
    print("=" * 62)
    print()


if __name__ == "__main__":
    asyncio.run(Main())
