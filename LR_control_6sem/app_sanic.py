from sanic import Sanic
from sanic.response import json
import asyncio
import time

app = Sanic("cpu_benchmark")

def cpu_task():
    """Синхронная CPU-задача"""
    return sum(range(1, 15_000_001))

@app.route("/cpu", methods=["GET"])
async def cpu_blocking(request):
    """ПЛОХО: Блокирующая версия - заморозит event loop"""
    start = time.time()
    result = cpu_task()
    elapsed = time.time() - start
    return json({
        "result": result,
        "elapsed": elapsed,
        "type": "blocking (BAD for async)"
    })

@app.route("/cpu_fixed", methods=["GET"])
async def cpu_nonblocking(request):
    """ХОРОШО: Неблокирующая версия с выносом в поток"""
    start = time.time()
    loop = asyncio.get_event_loop()
    # Выносим CPU-задачу в отдельный поток
    result = await loop.run_in_executor(None, cpu_task)
    elapsed = time.time() - start
    return json({
        "result": result,
        "elapsed": elapsed,
        "type": "non-blocking (with executor)"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, workers=1, access_log=False, debug=False)