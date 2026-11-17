FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY src ./src
COPY app ./app
COPY models ./models
COPY web ./web
COPY analysis/outputs_s16 ./analysis/outputs_s16
EXPOSE 8000
CMD gunicorn app.api:app --bind 0.0.0.0:${PORT} --workers 2 --timeout 60
