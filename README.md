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
    image: hroost/ovh_ip-mitigation_exporter:latest
    container_name: ovh_exporter
    ports:
      - "9298:9298"
    environment:
      - APPLICATION_KEY=xxxxxxxxxxx
      - APPLICATION_SECRET=xxxxxxxxxxxxxxxxxxxxxx
      - CONSUMER_KEY=xxxxxxxxxxxxxxxxxxxxxx
```

## How to Use:

1. Generate OVH API tokens with their pages
   - https://eu.api.ovh.com/createToken/ - for EU region
   - https://ca.api.ovh.com/createToken/ - for CA region
   - https://api.ovh.com/createToken/ - for US region

You'll want to grant a GET request to the following OVH API URL: ```/me``` ```/ip``` ```/ip/*```.

Further documentation on the ```/ip/{ipBlock}/mitigation/{ipAddr}``` API endpoint can be found on OVH's API
documentation page here: https://api.ovh.com/console/#/ip/{ip}/mitigation/{ipOnMitigation}#GET

2. Use the keys generated and configure them in docker-compose.yml
3. docker-compose up
