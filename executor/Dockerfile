FROM python:3.13-slim

COPY --from=docker:28-cli /usr/local/bin/docker /usr/local/bin/docker

WORKDIR /opt/executor

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "executor.main:app", "--host", "0.0.0.0", "--port", "8000"]
