FROM python:3

RUN pip install ovh && \
    pip install pytz && \
    pip install python-dateutil && \
    pip install prometheus_client

ADD exporter.py /

EXPOSE 9298/tcp

CMD [ "python", "-u", "./exporter.py" ]