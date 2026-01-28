# Use lightweight Python 3.11
FROM python:3.11-slim

# Disable Python bytecode generation and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Copy application source code
COPY main_EN_1.0.4.py .

# Copy SQLite database file
COPY management_system.db .

# Run the application
CMD ["python", "main_EN_1.0.4.py"]
