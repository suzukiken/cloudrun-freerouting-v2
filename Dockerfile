FROM alpine/java:21-jre

ENV PYTHONUNBUFFERED True

RUN apk update
RUN apk add bash
RUN apk add --no-cache python3
RUN apk add --no-cache py3-tornado
RUN apk add --no-cache py3-psutil

WORKDIR /opt

ADD freerouting-2.1.0.jar /opt/freerouting-2.1.0.jar
ADD main.py /opt/main.py
ADD sample.dsn /opt/sample.dsn
ADD single.rules /opt/single.rules
ADD bottom.rules /opt/bottom.rules
ADD ignore.rules /opt/ignore.rules

CMD [ "python3", "main.py" ]