FROM python:3.13-slim

WORKDIR /app

ARG REQUIREMENTS=requirements.txt

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r $REQUIREMENTS

COPY . .

EXPOSE 8000

CMD ["gunicorn", "bookstore.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
