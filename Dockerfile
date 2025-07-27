# Use lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary source code
COPY extract_outline.py .
COPY input/ ./input/
COPY output/ ./output/

# Set default command
CMD ["python", "extract_outline.py"]
