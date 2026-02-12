FROM python:3.11-slim

WORKDIR /app

COPY tap_api.py .

RUN pip install --no-cache-dir flask

EXPOSE 5001

CMD ["python", "tap_api.py"]
