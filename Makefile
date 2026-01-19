up:
	docker-compose up -d
	@echo "✅ Контейнеры запущены: http://localhost:8000"

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-ollama:
	docker-compose logs -f ollama

logs-api:
	docker-compose logs -f api

health:
	docker-compose ps

dev:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

migrate:
	poetry run alembic upgrade head

migration:
	poetry run alembic revision --autogenerate

clean:
	docker-compose down -v --rmi all

.DEFAULT_GOAL := up
