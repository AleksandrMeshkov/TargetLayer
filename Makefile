up:
	docker-compose up -d
	@docker exec targetlayer_ollama ollama pull phi3:mini 2>/dev/null
	@echo "✅ Все запущено: http://localhost:8000"

down:
	docker-compose down

logs:
	docker-compose logs -f

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
