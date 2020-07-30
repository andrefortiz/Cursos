FROM python:3.7

RUN apt-get update && apt-get upgrade -y
#RUN apt-get install -y --no-install-recommends apt-utils
#RUN apt-get clean

#RUN apt-get install python3-dev -y;
#RUN apt-get install python3-pip -y;
#RUN pip3 install pip;

RUN apt-get install build-essential;
RUN apt-get install gcc;
RUN apt-get install libc-dev;
#RUN apt-get install linux-headers;
RUN apt-get install uwsgi-plugin-python3 -y;


COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /usr/src
RUN mkdir -p /usr/tests
RUN mkdir -p /usr/db
WORKDIR /usr/src

COPY src /usr/src/
RUN pip install -e /usr/src
COPY tests /usr/tests/


CMD ["uwsgi", "app.ini"]

#ENV FLASK_ENV=development
#ENV FLASK_APP=src/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1
#CMD ["dockerproject", "run", "--host=0.0.0.0"]
