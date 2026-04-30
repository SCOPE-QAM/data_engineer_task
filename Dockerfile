FROM python:3.10

WORKDIR /app

ENV PYTHONPATH=/app

RUN pip install poetry

# copy only dependency files
COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --with dev --no-root --no-interaction --no-ansi

# now copy the code
COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
