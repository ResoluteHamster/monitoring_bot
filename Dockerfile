ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION:-3.10.10}-slim-bullseye

ENV TZ=Europe/Moscow
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_NO_CACHE_DIR=off
ENV PYTHONDONTWRITEBYTECODE=on
ENV PYTHONFAULTHANDLER=on
ENV PYTHONUNBUFFERED=on

ENV POETRY_VERSION=1.4.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV POETRY_NO_INTERACTION=1

COPY . /app/
WORKDIR /app/

RUN pip install "poetry==$POETRY_VERSION" && poetry config virtualenvs.create false
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Dependencies
COPY pyproject.toml poetry.loc[k] /app/
RUN poetry install --no-root --no-cache --without dev -vvv

CMD ["poetry", "run","python", "src/main.py"]

