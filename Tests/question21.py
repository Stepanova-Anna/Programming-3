from locust import HttpUser, task, between


class ApiUser(HttpUser):

    wait_time = between(1, 3)

    host = "http://localhost:8000"

    def on_start(self):
        print("Load testing started")

    @task
    def get_users(self):

        with self.client.get("/api/users", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                print("Request successful")
            else:
                response.failure(f"Request failed with status: {response.status_code}")

    def on_stop(self):
        print("Load testing finished")


def print_info():
    print("Locust test initialized")


if __name__ == "__main__":
    print_info()
