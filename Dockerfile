# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies first (before copying app files)
RUN apt-get update && apt-get install -y wkhtmltopdf

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Set environment variable for pdfkit
ENV WKHTMLTOPDF_PATH /usr/bin/wkhtmltopdf

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
