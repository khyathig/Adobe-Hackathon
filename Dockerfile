# Use the official Python image
FROM python:3.10-slim-bullseye

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container
COPY ./src .

# The command to execute when the container starts
CMD ["python", "main.py"]