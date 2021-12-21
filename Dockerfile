FROM python:3.9

RUN pip install ovh && \
    pip install prometheus_client

ADD exporter.py /

EXPOSE 9298/tcp

CMD [ "python", "-u", "./exporter.py" ]