import httpx
import asyncio
import time

MainAPI = "http://127.0.0.1:8000"
FakeAPI = "http://127.0.0.1:8001"


async def SetLLMMode(Mode: str):
    async with httpx.AsyncClient(timeout=5) as C:
        await C.post(f"{FakeAPI}/mode/{Mode}")
    print(f"[Config] LLM switched to: {Mode}")


async def HitRawEndpoint(UserTag: str, GlobalStart: float):
    print(f"  [{UserTag}] Request fired at t=+{time.time() - GlobalStart:.1f}s")
    try:
        async with httpx.AsyncClient(timeout=70) as C:
            R = await C.get(f"{MainAPI}/raw-summary", params={"Prompt": "summarize my notes"})
        Elapsed = time.time() - GlobalStart
        print(f"  [{UserTag}] Response after {Elapsed:.1f}s — waited full timeout, no fallback given")
    except httpx.TimeoutException:
        Elapsed = time.time() - GlobalStart
        print(f"  [{UserTag}] Timed out after {Elapsed:.1f}s — user got nothing at all!")
    except Exception as E:
        print(f"  [{UserTag}] Error: {E}")


async def Main():
    print()
    print("=" * 58)
    print("  DEMO: Without Circuit Breaker  — Broken Behavior")
    print("=" * 58)

    await SetLLMMode("slow")
    await asyncio.sleep(0.5)

    print("[Info] All 3 users hitting /raw-summary (no circuit breaker)")
    print("[Info] LLM is slow — each user will wait the full 60s...")
    print()

    GlobalStart = time.time()
    await asyncio.gather(
        HitRawEndpoint("User-1", GlobalStart),
        HitRawEndpoint("User-2", GlobalStart),
        HitRawEndpoint("User-3", GlobalStart),
    )

    Total = time.time() - GlobalStart
    print()
    print("=" * 58)
    print(f"  RESULT: All 3 users waited ~{Total:.0f}s with zero fallback")
    print("  This is exactly what the circuit breaker prevents")
    print("=" * 58)

    await SetLLMMode("normal")
    print("[Config] LLM switched back to normal mode")


if __name__ == "__main__":
    asyncio.run(Main())
