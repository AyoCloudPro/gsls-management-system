FROM python:3.9

WORKDIR /app

# Install system dependencies including wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf
ENV PATH="/usr/local/bin:$PATH"

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
