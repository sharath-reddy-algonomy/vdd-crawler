FROM python:3.11-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

#CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
ENTRYPOINT ["./entrypoint.sh"]