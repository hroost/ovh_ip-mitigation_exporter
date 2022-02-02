# -*- encoding: utf-8 -*-
#
# pip install ovh
# pip install prometheus_client
#

from prometheus_client import start_http_server
from prometheus_client import Gauge
from prometheus_client import REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR

import time
import ovh
import os
import sys

# -------------------------------------------------------
# Check if IP is IPV4
# -------------------------------------------------------
def isgoodipv4(ipString):
    pieces = ipString.split('.')
    if len(pieces) != 4:
      return False
    try:
      return all(0<=int(p)<256 for p in pieces)
    except ValueError:
      return False

# -------------------------------------------------------
# Reset local cache
# -------------------------------------------------------
def resetCacheState(cache, accountName):
  for ip in cache:
    GaugeIpOnMitigation.labels(accountName, cache[ip]['ip'], cache[ip]['ipblock']).set(0)

# -------------------------------------------------------
# Count mitigation IPs
# -------------------------------------------------------
def getAccountName():
  sys.stdout.write("Getting account name...\n")
  try:
    return client.get('/me')['nichandle']

  except Exception as e:
    sys.stderr.write('error:'+str(e))
    exit(1)

# -------------------------------------------------------
# Count mitigation IPs
# -------------------------------------------------------
def getIPsOnMitigation(accountName, cache):
  sys.stdout.write("Searching IPs on mitigation...\n")

  countOnMitigation = 0

  try:
    # Get all IPs
    ips = client.get('/ip')

    # Reset internal cache
    resetCacheState(cache, accountName)

    for ipnet in ips:
        # filter IPV4
        if not isgoodipv4(ipnet.split('/', 1)[0]):
          continue
        try:
          # Get ip/ipnet mitigation status
          resp = client.get('/ip/' + ipnet.replace('/', '%2F') + '/mitigation', auto=True)
          for ipaddr in resp:
            sys.stdout.write('- IP:'+ipaddr+'\n')
            countOnMitigation = countOnMitigation + 1

            GaugeIpOnMitigation.labels(accountName, ipaddr, ipnet).set(1)
            cache[ipaddr] = {"ip": ipaddr, "ipblock": ipnet}

        except ovh.exceptions.ResourceNotFoundError:
          continue
        except ovh.exceptions.ResourceExpiredError:
          continue

    sys.stdout.write(str(countOnMitigation) + " IPs on mitigation found\n")
    GaugeIpCountOnMitigation.labels(accountName).set(countOnMitigation)

  except Exception as e:
    sys.stderr.write('error:'+str(e))
    exit(1)

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():

  # Start up the server to expose the metrics.
  start_http_server(port)

  accountName = getAccountName()
  cache = {}
  # Generate some requests.
  while True:
      getIPsOnMitigation(accountName, cache)
      time.sleep(interval)

# -------------------------------------------------------
# RUN
# -------------------------------------------------------

# http port - default 9298
port = int(os.getenv('PORT', 9298))

# Refresh interval between collects in seconds - default 60
interval = int(os.getenv('INTERVAL', 60))

application_key = os.getenv('APPLICATION_KEY', None)
application_secret = os.getenv('APPLICATION_SECRET', None)
consumer_key = os.getenv('CONSUMER_KEY', None)

if not application_key:
  sys.stderr.write("Application key is required please set APPLICATION_KEY environment variable.\n")
  exit(1)

if not application_secret:
  sys.stderr.write("Application secret is required please set APPLICATION_SECRET environment variable.\n")
  exit(1)

if not consumer_key:
  sys.stderr.write("cosumer key is required please set CONSUMER_KEY environment variable.\n")
  exit(1)

# Show init parameters
sys.stdout.write('----------------------\n')
sys.stdout.write('Init parameters\n')
sys.stdout.write('port : ' + str(port) + '\n')
sys.stdout.write('interval : ' + str(interval) + 's\n')
sys.stdout.write('----------------------\n')

# OVH credentials
client = ovh.Client(
    endpoint='ovh-eu',
    application_key=application_key,
    application_secret=application_secret,
    consumer_key=consumer_key
)

# Disable default python metrics
REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)

# Create gauge
GaugeIpOnMitigation = Gauge('ovh_ip_onmitigation', 'IPs on OVH mitigation due attacks', ['account', 'ip', 'ipblock'])
GaugeIpCountOnMitigation = Gauge('ovh_ipcount_onmitigation', 'Count IPs on OVH mitigation due attacks', ['account'])

if __name__ == '__main__':
  main()
