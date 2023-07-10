FROM python:3.11-alpine

LABEL org.opencontainers.image.source = "https://github.com/hroost/ovh_ip-mitigation_exporter"

RUN pip install ovh && \
    pip install prometheus_client

ADD exporter.py /

EXPOSE 9298/tcp

CMD [ "python", "-u", "./exporter.py" ]
