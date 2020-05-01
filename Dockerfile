FROM python:2

RUN pip install ovh && \
    pip install prometheus_client

ADD exporter.py /

CMD [ "python", "-u", "./exporter.py" ]