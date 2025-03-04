#!/bin/sh
echo "🔍 Checking Environment Variables..."
echo "SECRET_KEY: $SECRET_KEY"
echo "DATABASE_URL: $DATABASE_URL"

echo "⏳ Running Migrations..."
flask db upgrade

echo "🚀 Starting Flask App..."
exec gunicorn -w 4 -b 0.0.0.0:8080 app:app
