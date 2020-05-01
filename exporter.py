# -*- encoding: utf-8 -*-
#
# pip install ovh
# pip install prometheus_client
#

from prometheus_client import start_http_server
from prometheus_client import Gauge
from prometheus_client import REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR

import time
import json
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
# Count blocked IPs
# -------------------------------------------------------
def getBlockedIPs():
  sys.stdout.write("Searching blocked IPs...\n")

  # Get all IPs
  ips = client.get('/ip')

  countBlocked = 0

  for ip in ips:
      # filter IPV4
      if not isgoodipv4(ip.split('/', 1)[0]):
        continue
      try:
        # Get spam ip
        spamip = client.get('/ip/' + ip.split('/', 1)[0] + '/spam')
        if spamip:
          # Get spam ip information
          spamipinfo = client.get('/ip/' + ip.split('/', 1)[0] + '/spam/' + spamip[0])
          if spamipinfo['state'] == "blocked":
            countBlocked = countBlocked + 1
      except ovh.exceptions.ResourceNotFoundError:
        continue
      except Exception as e:
        sys.stderr.write(e)
        continue

  sys.stdout.write(str(countBlocked) + " blocked IPs found\n")
  return countBlocked

# -------------------------------------------------------
# Set Gauge blocked IPs value
# -------------------------------------------------------
def setGaugeBlockedIPs():
  GaugeBlockedIPs.set(getBlockedIPs())

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():

  # Start up the server to expose the metrics.
  start_http_server(port)

  # Generate some requests.
  while True:
      setGaugeBlockedIPs()
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
GaugeBlockedIPs = Gauge('ovh_spam_blocked_ip', 'Count Blocked IPs due to spam')

if __name__ == '__main__':
  main()
