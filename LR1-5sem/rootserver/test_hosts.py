import sys
import requests

# Добавляем путь к activation_script
sys.path.insert(0, '..')

# Импортируем наш хук
from activation_script import enhanced_url_hook

sys.path_hooks.append(enhanced_url_hook)


def test_remote_imports():
    """Тестирует импорт с разных хостов"""

    test_hosts = [
        "http://localhost:8000",  # Локальный сервер
        "https://replit.com/@stepanna/LR1-prog-5",
    ]

    for host in test_hosts:
        try:
            print(f"\n=== Тестируем хост: {host} ===")
            sys.path.append(host)

            # Пробуем импортировать наш модуль
            try:
                import myremotemodule
                result = myremotemodule.myfoo()
                print(f"Успех: {result}")
            except ImportError as e:
                print(f"Модуль не найден: {e}")
            except Exception as e:
                print(f"Ошибка импорта: {e}")

            # Убираем хост из пути
            sys.path.remove(host)

        except Exception as e:
            print(f"Ошибка хоста {host}: {e}")


if __name__ == "__main__":
    test_remote_imports()