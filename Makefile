.PHONY: test test-fast test-slow test-all help

help:
	@echo "Available commands:"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run fast tests (default, excludes slow tests)"
	@echo "  make test-fast   - Run fast tests only"
	@echo "  make test-slow   - Run slow tests only"
	@echo "  make test-all    - Run all tests (including slow)"
	@echo ""
	@echo "Database:"
	@echo "  make init-db      - Initialize database"
	@echo "  make create-indexes - Create database indexes"
	@echo "  make verify-indexes - Verify database indexes"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start all services"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-logs  - View app logs"
	@echo "  make docker-restart - Restart app service"
	@echo "  make docker-clear-db - Clear database (keep volumes)"
	@echo "  make docker-reset   - Reset everything (remove volumes and restart)"
	@echo ""
	@echo "Services:"
	@echo "  make check-services - Check service health"

test: test-fast

test-fast:
	@source venv/bin/activate && pytest tests/ -v -m "not slow"

test-slow:
	@source venv/bin/activate && pytest tests/ -v -m "slow"

test-all:
	@source venv/bin/activate && pytest tests/ -v

init-db:
	@source venv/bin/activate && python scripts/init_db.py

create-indexes:
	@source venv/bin/activate && python scripts/create_indexes.py

verify-indexes:
	@source venv/bin/activate && python scripts/verify_indexes.py

check-services:
	@bash scripts/check_services.sh

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-restart:
	docker-compose restart app

docker-clear-db:
	@docker-compose exec app python scripts/clear_db.py 2>/dev/null || \
	docker-compose run --rm app python scripts/clear_db.py

docker-reset:
	docker-compose down -v
	docker-compose up -d

