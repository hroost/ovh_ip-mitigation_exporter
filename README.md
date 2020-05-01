# ovh-exporter

Docker image to export metrics from OVH API to prometheus

**Parameters**

- port : http port (default : 9298)
- interval : interval between collect in seconds (default: 60)
- application_key : OVH API application key
- application_secret : OVH API application secret
- consumer_key : OVH API consumer key

**docker compose sample**

```yml
version: "2.1"

services:

  ovh_exporter:
    image: leberrem/ovh_exporter;latest
    container_name: ovh_exporter
    ports:
      - "9298:9298"
    environment:
      - APPLICATION_KEY=xxxxxxxxxxx
      - APPLICATION_SECRET=xxxxxxxxxxxxxxxxxxxxxx
      - CONSUMER_KEY=xxxxxxxxxxxxxxxxxxxxxx
```