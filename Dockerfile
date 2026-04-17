FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY examples/idun_compress_agent/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY examples/idun_compress_agent/ /app/

RUN chmod +x /app/docker_entrypoint.sh

EXPOSE 8800

CMD ["/app/docker_entrypoint.sh"]
