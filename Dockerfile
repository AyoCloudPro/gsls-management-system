# Use an official lightweight Python image
FROM python:3.11-slim AS base

# Copy requirements.txt first for better caching
COPY requirements.txt /tmp/

# Install dependencies before copying the app (leverages Docker cache)
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory inside the container
WORKDIR /app

# Copies the rest of the application files
COPY . .

# Expose the port Flask will run on
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Use Gunicorn to serve the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
