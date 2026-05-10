Mohsin Fawad | BSCS23161

# PDC-Sp24-BSCS23161-Fawad

**Student:** Mohsin Fawad  
**ID:** BSCS23161  
**Course:** Parallel and Distributed Computing  
**Assignment:** Building Resilient Distributed Systems  

## Problem Chosen

Problem 3 — Fault Tolerance (Frozen Server)  
Implements the Circuit Breaker pattern so a crashed LLM API cannot freeze the entire server.

## Files

| File | Purpose |
|------|---------|
| app.py | FastAPI backend with circuit breaker + X-Student-ID middleware |
| breaker.py | Circuit breaker class (CLOSED / OPEN / HALF_OPEN states) |
| fake_llm.py | Fake LLM server to simulate normal, slow, and crashed behavior |
| demo_broken.py | Proves the problem — users wait 60s with zero fallback |
| demo_fixed.py | Proves the fix — instant fallback once breaker trips |

## How to Run

**Step 1 — Install dependencies**

```
pip install fastapi uvicorn httpx
```

**Step 2 — Open 3 terminals**

Terminal 1 (fake LLM server):
```
python fake_llm.py
```

Terminal 2 (main API):
```
python app.py
```

Terminal 3 — to see the broken behavior first:
```
python demo_broken.py
```

Then to see the circuit breaker fix:
```
python demo_fixed.py
```

## Verifying X-Student-ID Header

Visit http://127.0.0.1:8000/health in your browser.  
Open DevTools → Network tab → click the request → Response Headers → you will see:  
`X-Student-ID: BSCS23161`

Every single endpoint returns this header via middleware.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /generate-summary | GET | LLM call protected by circuit breaker |
| /raw-summary | GET | LLM call with no protection (used by demo_broken.py) |
| /breaker-status | GET | Shows current breaker state and fail count |
| /breaker-reset | POST | Resets breaker back to CLOSED |
| /health | GET | Basic health check |

## Circuit Breaker States

| State | What It Means |
|-------|---------------|
| CLOSED | Everything working fine, requests reach the LLM |
| OPEN | LLM is not responding, user gets an immediate fallback message |
| HALF_OPEN | Waiting period is over, one request sent to check if LLM recovered |
