from locust import HttpUser, task, between

class HabrUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://habr.com"

    def on_start(self):
        print("Habr load test started")

    @task
    def load_main_page(self):
        with self.client.get("/ru", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                print("Page loaded: /ru")
            else:
                response.failure(f"Page failed with status: {response.status_code}")

    def on_stop(self):
        print("Habr load test finished")
