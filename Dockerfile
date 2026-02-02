FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
# Ensure requests is installed (redundant if in requirements but explicit for reliability)
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir requests
COPY . /app
EXPOSE 8080
CMD ["bash","-c","python app.py"]
