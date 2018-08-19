FROM python:3.6-stretch

ENV PYTHONPATH $PYTHONPATH:/var/app

WORKDIR /var/app

COPY . ./

RUN apt-get update && \
    apt-get install -y bash musl-dev libc-dev gcc git && \
    pip3 install -U pip && \
    pip3 install -r requirements.txt

EXPOSE 8000

CMD ./bin/boot
