# Use full Python image for building
FROM python:3.9 AS builder

WORKDIR /app

# Install system dependencies (remove wkhtmltopdf)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies in a virtual environment
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Use a lightweight final image
FROM python:3.9-slim

WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Copy and set permissions for entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables (remove WKHTMLTOPDF_PATH)
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8080

# Run Gunicorn with multiple workers
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
