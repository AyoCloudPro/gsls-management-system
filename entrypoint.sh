#!/bin/sh
echo "Waiting for MySQL to start..."
while ! nc -z mysql-container 3306; do
  sleep 1
done
echo "MySQL is up! Starting Flask..."

# Apply migrations
flask db upgrade

# Start Gunicorn
exec gunicorn -w 4 -b 0.0.0.0:8080 app:app
