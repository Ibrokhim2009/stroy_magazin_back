FROM python:3.13-slim

WORKDIR /core

COPY . /core

RUN pip install -r requirements.txt 

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]