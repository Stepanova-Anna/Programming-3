from quart import Quart, jsonify
import asyncio
import time

app = Quart(__name__)

def cpu_task():
    """Синхронная CPU-задача"""
    return sum(range(1, 15_000_001))

@app.route('/cpu', methods=['GET'])
async def cpu_blocking():
    """ПЛОХО: Блокирующая версия"""
    start = time.time()
    result = cpu_task()  # Блокирует event loop
    elapsed = time.time() - start
    return jsonify({
        "result": result,
        "elapsed": elapsed,
        "type": "blocking (BAD for async)"
    })

@app.route('/cpu_fixed', methods=['GET'])
async def cpu_nonblocking():
    """ХОРОШО: Неблокирующая версия"""
    start = time.time()
    loop = asyncio.get_event_loop()
    # Выносим в отдельный поток
    result = await loop.run_in_executor(None, cpu_task)
    elapsed = time.time() - start
    return jsonify({
        "result": result,
        "elapsed": elapsed,
        "type": "non-blocking (with executor)"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)