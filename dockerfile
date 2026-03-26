FROM ddrc8v9auy82k5.xuanyuan.run/library/python:alpine3.16
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]