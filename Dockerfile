FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

CMD ["./start.sh"]