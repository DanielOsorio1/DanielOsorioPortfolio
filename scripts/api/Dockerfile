FROM python:3.11-slim

WORKDIR /app

COPY tap_api.py .

RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir flask

EXPOSE 5001

CMD ["python", "tap_api.py"]
