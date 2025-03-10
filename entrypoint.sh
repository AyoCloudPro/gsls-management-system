#!/bin/sh
set -e  # Exit immediately if any command fails

# Ensure required environment variables exist
if [ -z "$SECRET_KEY" ] || [ -z "$DATABASE_URL" ]; then
  echo "❌ ERROR: Missing required environment variables!"
  exit 1
fi

echo "🔍 Checking Environment Variables..."
echo "SECRET_KEY: $SECRET_KEY"
echo "DATABASE_URL: $DATABASE_URL"

# Wait for the database to be ready
echo "⏳ Waiting for database to be ready..."
until nc -z -v -w30 "$(echo $DATABASE_URL | sed -E 's|.*://([^:/]+).*|\1|')" 5432; do
  echo "🔄 Database is unavailable - retrying in 5s..."
  sleep 5
done
echo "✅ Database is up!"

# Run database migrations
echo "⏳ Running Migrations..."
if flask db upgrade; then
  echo "✅ Migrations applied successfully!"
else
  echo "❌ ERROR: Migrations failed!"
  exit 1
fi

# Start the Flask app using Gunicorn
echo "🚀 Starting Flask App..."
exec gunicorn -w 4 -b 0.0.0.0:8080 app:app --access-logfile '-' --error-logfile '-'
