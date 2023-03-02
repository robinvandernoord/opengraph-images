FROM python:3.10-slim
RUN apt update && apt install -y wkhtmltopdf

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

RUN mkdir /code
WORKDIR /code

COPY server /code/server
COPY create.py /code/server/lib/create.py
COPY template.html /code/


EXPOSE 5000

CMD ["flask", "--app", "server", "run", "--host", "0.0.0.0", "--port", "5000"]
