FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    curl_cffi faker requests aiohttp pycryptodome fake_useragent \
    beautifulsoup4 luhn cryptography colorama psycopg2-binary

EXPOSE 8080

CMD ["python", "apis/server.py", "--host", "0.0.0.0", "--port", "8080"]