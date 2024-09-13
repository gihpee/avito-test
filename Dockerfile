FROM python:3.11-slim

WORKDIR /avito_test

COPY avito_test /avito_test
COPY requirements.txt /avito_test
COPY .env /avito_test

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8080

RUN python manage.py makemigrations service
RUN python manage.py migrate

CMD ["sh", "-c", "python manage.py runserver $SERVER_ADDRESS"]