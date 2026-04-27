FROM python:3.11-slim

WORKDIR /app

# Install git for git tools
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .
RUN mkdir -p workspace

EXPOSE 8000

CMD ["python", "-m", "app.main"]
