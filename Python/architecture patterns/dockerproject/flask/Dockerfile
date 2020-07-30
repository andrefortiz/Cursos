# Step 1: Import the Os
FROM alpine:3.7

# Step 2: Install pip and Python Dependencies
RUN apk add --no-cache python3-dev \
    && apk add --update py-pip \
    && pip3 install --upgrade pip

# Step 3: Create a Work Directory
RUN mkdir -p /usr/app
WORKDIR /usr/app

# Step 4: copy all Project Files
COPY . /usr/app

# Step 5: Install all Dependencies for WSGI
RUN set -e;
#RUN apk add --no-cache build-essential;
#RUN apk add --no-cache --virtual build-base;
RUN apk add --no-cache --virtual .build-deps;
RUN apk add --no-cache --virtual gcc;
#RUN apk add --no-cache --virtual clang;
RUN apk add --no-cache --virtual libc-dev;
RUN apk add --no-cache --virtual linux-headers;
RUN apk add --no-cache uwsgi-python3;


RUN pip install -r requirements.txt;
RUN apk del .build-deps;

# Step 6:  run the command to start uWSGI
CMD ["uwsgi", "app.ini"]

#no app.ini eu tive que incluir os parametros:
#plugin = python3: (esse para funcionar)
#uid = uwsgi (esse para para os warnings)