# Student Management System (Console Application)

A console-based **Student Management System** developed using **Python 3.11** and **SQLite**, designed to manage students, teachers, courses, schedules, and grades. The project is fully containerized using **Docker** for easy setup and deployment.

---

## 1. Features

### Admin

* Manage users (Students, Teachers, Admins)
* Manage subjects
* Manage course sections
* Manage class schedules
* View statistical reports
* Change password

### Teacher

* View assigned courses
* View teaching schedule
* Enter and update student grades
* Change password

### Student

* View personal profile
* View class schedule
* View enrolled courses and grades
* Change password

---

## 2. Technologies Used

* **Programming Language:** Python 3.11
* **Database:** SQLite 3
* **Containerization:** Docker
* **Application Type:** Console (CLI)

---

## 3. Project Structure

```text
project/
│── Dockerfile
│── main_EN_1.0.3.py
│── management_system.db
│── README.md
```

---

## 4. Requirements

* Docker installed on your system
* Windows / macOS / Linux

Check Docker installation:

```bash
docker --version
```

---

## 5. Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY main_EN_1.0.4.py .
COPY management_system.db .

CMD ["python", "main_EN_1.0.4.py"]
```

---

## 6. Build the Docker Image

Run the following command in the project directory:

```bash
docker build -t student-management .
```

---

## 7. Run the Application

### Basic Run

```bash
docker run -it student-management
```

### Recommended (Persistent Database)

```bash
docker run -it \
  -v $(pwd)/management_system.db:/app/management_system.db \
  student-management
```

> This ensures that database data is not lost when the container stops.

---

## 8. Default Accounts

### Admin Account

```
Username: admin
Password: admin123
```

> Admin can create Student and Teacher accounts from the system menu.

---

## 9. Database Notes

* The system uses **SQLite**, no external database server required
* All tables are stored in `management_system.db`
* The database schema must match the SQL queries used in the source code

---

## 10. Common Issues & Solutions

### Docker build fails: "Dockerfile not found"

* Ensure the file name is exactly `Dockerfile` (no extension)

### Data lost after container stops

* Use Docker volume mounting (`-v` option)

### SQLite errors: "no such column"

* Database schema does not match the code
* Check table structure using:

```sql
PRAGMA table_info(TableName);
```

---

## 11. Usage Notes

* Time format: **HH:MM (24-hour format)**
* Grade scale: **0.0 – 10.0**
* Passing grade: **≥ 4.0**
* Console input is case-sensitive in some fields

---

## 12. Future Improvements

* Password hashing (bcrypt)
* Pagination for large lists
* Migration to MySQL/PostgreSQL
* Docker Compose support
* Role-based access control refinement

---

## 13. License

This project is intended for **educational purposes only**.

---

## 14. Author

Developed as a course project using Python and Docker.
