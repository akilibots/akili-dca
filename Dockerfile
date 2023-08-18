FROM python:3.9

RUN pip install dydx-v3-python==2.0.1 pyjson5==1.6.3

WORKDIR /app
COPY . .

CMD ["python3","-u","app.py"]