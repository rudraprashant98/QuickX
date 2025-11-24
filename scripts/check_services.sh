#!/bin/bash

echo "=== Checking Docker Services ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running"
    echo "   Please start Docker Desktop"
    exit 1
fi
echo "✓ Docker is running"
echo ""

# Check services status
echo "Service Status:"
docker-compose ps
echo ""

# Check if app is accessible
echo "Testing API endpoint..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✓ API is accessible on http://localhost:8000"
else
    echo "✗ API is not accessible"
    echo ""
    echo "Checking app logs..."
    docker-compose logs --tail=50 app
fi
echo ""

# Check database
echo "Testing database connection..."
if docker-compose exec -T postgres pg_isready -U robotics > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "✗ PostgreSQL is not ready"
fi
echo ""

# Check Redis
echo "Testing Redis..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready"
else
    echo "✗ Redis is not ready"
fi
echo ""

# Check RabbitMQ
echo "Testing RabbitMQ..."
if docker-compose exec -T rabbitmq rabbitmqctl status > /dev/null 2>&1; then
    echo "✓ RabbitMQ is ready"
else
    echo "✗ RabbitMQ is not ready"
fi
echo ""

echo "=== Service Check Complete ==="
echo ""
echo "To start services: docker-compose up -d"
echo "To view logs: docker-compose logs -f app"
echo "To restart: docker-compose restart app"

