import subprocess
import time
import os
import sys

PORTS = {
    5000: "Flask",
    8000: "Sanic",
    8080: "Quart"
}

USERS = [50]
TEST_DURATION = "3m"


def run_locust_test(port, users):
    """Запуск Locust теста для конкретного порта и количества пользователей"""

    print(f"Тестирование: {PORTS[port]} (порт {port}) с {users} пользователями")

    csv_prefix = f"results_{PORTS[port].lower()}_{users}"

    # Команда для запуска Locust
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--headless",
        "--users", str(users),
        "--spawn-rate", str(users),
        "--run-time", TEST_DURATION,
        "--port", str(port),
        "--csv", csv_prefix,
        "--only-summary",
        "--host", f"http://localhost:{port}"
    ]

    print(f"Запуск команды: {' '.join(cmd)}")

    try:
        # Запускаем тест
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Сохраняем вывод в файл
        with open(f"{csv_prefix}_output.txt", "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)

        print(f"Тест завершен. Результаты сохранены в {csv_prefix}_stats.csv")
        return True

    except Exception as e:
        print(f"Ошибка при выполнении теста: {e}")
        return False


def main():
    """Основная функция для запуска всех тестов"""
    print("НАЧАЛО СТРЕСС-ТЕСТИРОВАНИЯ")
    print(f"Тестируемые фреймворки: {', '.join(PORTS.values())}")
    print(f"Количество пользователей: {USERS}")
    print(f"Длительность теста: {TEST_DURATION} на сценарий")

    # Для каждого фреймворка и количества пользователей
    for port, framework in PORTS.items():
        print(f"\nПроверяем доступность {framework} на порту {port}...")

        # Проверяем, запущен ли сервер
        import requests
        try:
            response = requests.get(f"http://localhost:{port}/cpu", timeout=5)
            print(f"Сервер {framework} доступен")
        except:
            print(f"Сервер {framework} НЕ ДОСТУПЕН! Запустите сервер перед тестированием.")
            print(f"Команда для запуска: python app_{framework.lower()}.py")
            continue

        for users in USERS:
            run_locust_test(port, users)
            # Пауза между тестами для восстановления
            time.sleep(5)

    print("\nВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
    print("Сгенерированные файлы:")
    for file in os.listdir('.'):
        if file.startswith('results_') and (file.endswith('.csv') or file.endswith('.txt')):
            print(f"   - {file}")


if __name__ == "__main__":
    main()