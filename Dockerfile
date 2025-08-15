FROM python:alpine3.22

WORKDIR /app

COPY requirements.txt .

RUN apk add --no-cache bash && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--forwarded-allow-ips", "*", "--config", "gunicorn.conf.py", "app:create_app()"]