"""
Load test for Amagi: N users connected to one room, each sending messages.

Setup (backend only, no frontend needed):
  1. Postgres up and migrated (`alembic upgrade head` seeds the `general` room).
  2. Raise the login rate limit for the test, or every login after the 10th
     from your IP gets HTTP 429. In api/.env:
         LOGIN_MAX_ATTEMPTS=100000
     then start the API (`uvicorn app.main:app`). Put it back afterwards.
     Under docker compose api/.env is not passed to the container: add the
     variable to the `api` service's `environment` instead.
  3. From api/, with the venv from `uv sync --extra dev` (it has httpx and websockets):
         python app/services/load_test.py --users 100 --messages 5
     Increase --users (100, 250, 500, 1000...) until errors appear or p95
     latency climbs past what you consider acceptable (e.g. 500 ms).

Run each level 2-3 times and note your hardware (CPU, RAM) with the result.
"""

import argparse
import asyncio
import json
import random
import statistics
import time
import uuid

import httpx
from websockets.asyncio.client import connect

API = "http://localhost:8000/api/v1"
WS = "ws://localhost:8000/api/v1/ws"


async def make_user(client: httpx.AsyncClient, sem: asyncio.Semaphore) -> str:
    """Register a throwaway user and return its access token."""
    async with sem:
        name = f"lt_{uuid.uuid4().hex[:12]}"
        password = "loadtest123"
        r = await client.post(f"{API}/users/register", json={"username": name, "password": password})
        r.raise_for_status()
        r = await client.post(f"{API}/users/token", data={"username": name, "password": password})
        r.raise_for_status()
        return r.json()["access_token"]


async def run_client(token, room, n_messages, interval, start_evt, done_evt, stats):
    try:
        async with connect(f"{WS}/{room}", subprotocols=["bearer", token], open_timeout=30) as ws:
            stats["connected"] += 1

            async def reader():
                async for raw in ws:
                    frame = json.loads(raw)
                    text = frame.get("message", "")
                    if frame.get("type") == "message" and text.startswith("lt|"):
                        sent_at = float(text.split("|")[1])
                        stats["latencies"].append((time.perf_counter() - sent_at) * 1000)
                        stats["received"] += 1

            reader_task = asyncio.create_task(reader())
            await start_evt.wait()  # everyone connected before anyone sends
            # Spread the first send, or all N clients fire in lockstep every
            # interval and p95 measures that burst rather than steady load.
            await asyncio.sleep(random.uniform(0, interval))

            for _ in range(n_messages):
                await ws.send(json.dumps({"type": "message", "message": f"lt|{time.perf_counter()}"}))
                stats["sent"] += 1
                await asyncio.sleep(interval)

            await done_evt.wait()  # keep listening until the drain period ends
            if reader_task.done():
                # The server dropped this socket mid-test; without this it
                # still counts as connected and the failure is never reported.
                reader_task.result()  # re-raises the reader's own error, if any
                raise ConnectionError("closed by server")
            reader_task.cancel()
    except Exception as exc:  # noqa: BLE001
        stats["errors"].append(type(exc).__name__)


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--users", type=int, default=100)
    p.add_argument("--messages", type=int, default=5, help="messages per user")
    p.add_argument("--interval", type=float, default=1.0, help="seconds between a user's messages")
    p.add_argument("--room", default="general", help="an existing room slug")
    args = p.parse_args()

    stats = {"connected": 0, "sent": 0, "received": 0, "latencies": [], "errors": []}

    print(f"Creating {args.users} users...")
    sem = asyncio.Semaphore(20)
    async with httpx.AsyncClient(timeout=60) as client:
        tokens = await asyncio.gather(*(make_user(client, sem) for _ in range(args.users)))

    start_evt, done_evt = asyncio.Event(), asyncio.Event()
    tasks = [
        asyncio.create_task(run_client(t, args.room, args.messages, args.interval, start_evt, done_evt, stats))
        for t in tokens
    ]

    print("Connecting sockets...")
    deadline = time.time() + 60
    while stats["connected"] + len(stats["errors"]) < args.users and time.time() < deadline:
        await asyncio.sleep(0.2)
    print(f"Connected: {stats['connected']}/{args.users}")

    start_evt.set()
    await asyncio.sleep(args.messages * args.interval + 10)  # send window + drain
    done_evt.set()
    await asyncio.gather(*tasks, return_exceptions=True)

    connected = stats["connected"]
    expected = stats["sent"] * connected  # every message reaches every connected client, sender included
    lat = sorted(stats["latencies"])

    def pct(q):
        return lat[min(len(lat) - 1, int(q * len(lat)))] if lat else float("nan")

    print("\n--- Results ---")
    print(f"Concurrent sockets : {connected}/{args.users}")
    print(f"Messages sent      : {stats['sent']}")
    print(f"Deliveries         : {stats['received']}/{expected} "
          f"({100 * stats['received'] / expected if expected else 0:.1f}%)")
    if lat:
        print(f"Fan-out latency ms : p50={statistics.median(lat):.1f}  p95={pct(0.95):.1f}  p99={pct(0.99):.1f}")
    if stats["errors"]:
        print(f"Errors             : {len(stats['errors'])} -> {sorted(set(stats['errors']))}")


if __name__ == "__main__":
    asyncio.run(main())