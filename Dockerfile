# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install depemdemcies
RUN apt-get update && apt-get install -y wkhtmltopdf

# Copy the requirements file into the image
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the image
COPY . .

# Expose the port the app runs on
EXPOSE 80

# Set environment variable for pdfkit
ENV WKHTMLTOPDF_PATH C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe

# Command to run the application
CMD ["python", "app.py"]