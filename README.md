# **PhotoShare**

**PhotoShare** is a REST API for sharing photos, managing user profiles, and interacting with comments and ratings. Built using FastAPI, SQLAlchemy, and PostgreSQL, it provides a robust and scalable solution for managing photo-sharing platforms.

**Features**

User Authentication: Register, log in, and manage user profiles.

Photo Management: Upload, retrieve, and delete photos.

Tags: Add and manage tags for better organization and search.

Comments: Add, update, delete, and retrieve comments for photos.

Ratings: Allow users to rate photos and retrieve average ratings.

Admin Tools: Moderation tools for managing user-generated content.

---

**Technologies**

Backend: FastAPI

Database: PostgreSQL with SQLAlchemy

Environment Management: Poetry

Containerization: Docker and Docker Compose

---

**Prerequisites**

Before you begin, ensure you have the **following installed:**

Python 3.12+

Docker and Docker Compose

PostgreSQL database (or use a cloud-based solution like Koyeb)

---

**Installation and Setup**

Clone the Repository```bash

git clone https://github.com/zhendler/Switch_Crew.git

Install Poetry.
Enter in terminal: pip install --upgrade pip && pip install poetry

Install dependencies.
Enter in terminal: poetry install

Run app.
Enter in terminal: uvicorn main:app


**Installation and Setup with Docker**

Run docker container.
Enter in terminal: docker-compose up --build
