from locust import HttpUser, task, between
import random


class RecognitionUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # логин как teacher
        resp = self.client.post("/token/", data={"username": "admin", "password": "admin"})
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(1)
    def add_reference(self):
        # выбрать случайного студента
        student_id = random.choice([1, 2, 3, 4])
        with open("./test/reference_face.jpg", "rb") as f:
            files = {"photo": ("face.jpg", f, "image/jpeg")}
            self.client.post(f"/students/{student_id}/photos/", files=files, headers=self.headers)

    @task(2)
    def read_references(self):
        # выбрать случайного студента
        student_id = random.choice([1, 2, 3, 4])
        self.client.get(f"/students/{student_id}/photos/", headers=self.headers)