from locust import HttpUser, task, between, events
import argparse


class PerformanceUser(HttpUser):
    # wait_time = 0 означает максимальную нагрузку (без задержек)
    wait_time = between(0, 0)

    def on_start(self):
        """При старте пользователя определяем порт сервера"""
        self.port = self.environment.parsed_options.port
        self.host = f"http://localhost:{self.port}"

    @task(1)
    def cpu_endpoint(self):
        """Тестирование /cpu эндпоинта"""
        with self.client.get("/cpu",
                             name=f"Port {self.port} - /cpu",
                             catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Логируем тип выполнения
                    if data.get('type') == 'blocking':
                        response.success()
                except:
                    response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def cpu_fixed_endpoint(self):
        """Тестирование /cpu_fixed эндпоинта"""
        with self.client.get("/cpu_fixed",
                             name=f"Port {self.port} - /cpu_fixed",
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


@events.init_command_line_parser.add_listener
def add_port_argument(parser):
    """Добавляем возможность указывать порт через командную строку"""
    parser.add_argument("--port", type=int, required=True,
                        help="Port of the service (5000 for Flask, 8000 for Sanic, 8080 for Quart)")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Выводим информацию о начале теста"""
    port = environment.parsed_options.port
    print(f"\nStarting load test on port {port}")
    print(f"Users: {environment.parsed_options.num_users}")
    print(f"Run time: {environment.parsed_options.run_time}\n")