FROM python:3.12-slim

WORKDIR app
RUN apt-get update && apt-get install -y ffmpeg libffi-dev libnacl-dev python3-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend

EXPOSE 8080

ENTRYPOINT ["python", "-m", "backend.ports.discord.app"]