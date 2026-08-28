FROM python:3.13-slim

WORKDIR /app

ARG REQUIREMENTS=requirements.txt

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r $REQUIREMENTS

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

CMD ["/bin/sh", "docker/entrypoint.sh"]
