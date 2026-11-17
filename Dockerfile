FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN useradd -u 10001 -m appuser && mkdir -p /data && chown -R appuser:appuser /data
USER appuser
ENV PORT=8000 YAHWA_DB_PATH=/data/yahwa.sqlite3 YAHWA_HTTPS=1 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "server.py"]
