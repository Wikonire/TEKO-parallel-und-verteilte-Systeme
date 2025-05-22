# code/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY code/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY code/pi.py .
ENTRYPOINT ["python3", "pi.py"]
