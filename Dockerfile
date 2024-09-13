FROM python:3.11-slim

WORKDIR /avito_test

COPY avito_test /avito_test
COPY requirements.txt /avito_test

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "python manage.py makemigrations service && python manage.py migrate && python manage.py runserver"]