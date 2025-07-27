# Dockerfile
# Explicitly specify platform for compatibility
FROM --platform=linux/amd64 python:3.9-slim-bullseye

# Set working directory inside the container
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
# Use --no-cache-dir to keep image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/main.py ./src/main.py
# If you have other source files in src/, copy the whole directory:
# COPY src/ ./src/

# Define environment variable (optional)
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]