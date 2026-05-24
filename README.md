# TargetLayer

Backend API service (FastAPI) for the TargetLayer project.

## Development

- Install dependencies: `poetry install`
- Run locally: `poetry run uvicorn app.main:app --reload`

### Tests
python -m unittest discover -s app/tests/name_test -p "name_test.py"