from flask import Flask, jsonify
import time

app = Flask(__name__)

def cpu_intensive_task():
    """CPU-интенсивная задача: сумма чисел от 1 до 15 миллионов"""
    total = sum(range(1, 15_000_001))
    return total

@app.route('/cpu', methods=['GET'])
def cpu_endpoint():
    """Блокирующий эндпоинт - выполняется синхронно"""
    start = time.time()
    result = cpu_intensive_task()
    elapsed = time.time() - start
    return jsonify({
        "result": result,
        "elapsed": elapsed,
        "type": "blocking"
    })

@app.route('/cpu_fixed', methods=['GET'])
def cpu_fixed_endpoint():
    """Для синхронного Flask - то же самое блокирующее выполнение"""
    start = time.time()
    result = cpu_intensive_task()
    elapsed = time.time() - start
    return jsonify({
        "result": result,
        "elapsed": elapsed,
        "type": "blocking (sync framework limitation)"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=False, processes=1, debug=False)