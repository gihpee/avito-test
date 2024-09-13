FROM python:3.11-slim

WORKDIR /avito_test

COPY avito_test /avito_test
COPY requirements.txt /avito_test

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8080

ENV POSTGRES_CONN=${POSTGRES_CONN}
ENV POSTGRES_JDBC_URL=${POSTGRES_JDBC_URL}
ENV POSTGRES_USERNAME=${POSTGRES_USERNAME}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV POSTGRES_HOST=${POSTGRES_HOST}
ENV POSTGRES_PORT=${POSTGRES_PORT}
ENV POSTGRES_DATABASE=${POSTGRES_DATABASE}

ENV SERVER_ADDRESS=${SERVER_ADDRESS}

RUN python manage.py makemigrations service
RUN python manage.py migrate

CMD ["sh", "-c", "python manage.py runserver $SERVER_ADDRESS"]