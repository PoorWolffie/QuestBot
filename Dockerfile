FROM python:3.12-slim
WORKDIR usr/src/app

COPY . .

EXPOSE 8000

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]
