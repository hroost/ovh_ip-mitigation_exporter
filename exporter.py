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
import pytz
from datetime import datetime, timedelta
from dateutil import parser

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
# Forecast cost informations
# -------------------------------------------------------
def getForecastCost():
  sys.stdout.write("Searching Forecast...\n")

  allInstanceCost = 0
  allVolumeCost = 0

  lastMoth = datetime.now(pytz.utc) - timedelta(days=30)

  try:

    # Get account information
    account = client.get('/me')

    # Get projects
    projects = client.get('/cloud/project')

    for project in projects:

      # Get project info
      project_info = client.get('/cloud/project/'+project)

      instanceCost = 0

      # Get Instances from project
      instances = client.get('/cloud/project/'+project+'/instance')

      for instance in instances:

        # get price
        subsidiaryPrice = client.get('/cloud/subsidiaryPrice', flavorId=instance['flavorId'], ovhSubsidiary='FR',  region=instance['region'])

        if subsidiaryPrice['instances']:

          monthlyPrice = subsidiaryPrice['instances'][0]['monthlyPrice']['value']
          hourlyPrice = subsidiaryPrice['instances'][0]['price']['value']

          # select price
          if instance['monthlyBilling'] == None:
            price=round(hourlyPrice*24*31, 2)
            instanceCost = instanceCost + price
          else:
            price=round(monthlyPrice, 2)
            instanceCost = instanceCost + price

        else:

          sys.stdout.write("- INSTANCE: {'project': '"+project_info['description']+", 'region': '"+instance['region']+"', 'planCode': '"+instance['planCode']+"', 'name': '"+instance['name']+"'} - pas de prix trouvé \n")

      allInstanceCost = allInstanceCost + instanceCost

      volumeCost = 0

      # Get Volumes form project
      volumes = client.get('/cloud/project/'+project+'/volume')

      for volume in volumes:

        # select price
        if volume['type'] == 'high-speed':
          price=round(volume['size']*0.08, 2)
          volumeCost = volumeCost + price
        else:
          price=round(volume['size']*0.04, 2)
          volumeCost = volumeCost + price

      allVolumeCost = allVolumeCost + volumeCost

      sys.stdout.write("- INSTANCES: {'project': '"+project_info['description']+", 'cost': '"+str(round(instanceCost, 2))+"'}\n")
      GaugeForecastCost.labels(account['nichandle'], project_info['description'], 'instances').set(instanceCost)
      sys.stdout.write("- VOLUMES: {'project': '"+project_info['description']+", 'cost': '"+str(round(volumeCost, 2))+"'}\n")
      GaugeForecastCost.labels(account['nichandle'], project_info['description'], 'volumes').set(volumeCost)

    sys.stdout.write("Total instances cost" + str(round(allInstanceCost, 2)) + "\n")
    GaugeForecastCost.labels(account['nichandle'], 'total', 'instances').set(allInstanceCost)
    sys.stdout.write("Total volumes cost" + str(round(allVolumeCost, 2)) + "\n")
    GaugeForecastCost.labels(account['nichandle'], 'total', 'volumes').set(allVolumeCost)

  except Exception as e:
    sys.stderr.write('error:'+str(e))

# -------------------------------------------------------
# Count instances NotActive
# -------------------------------------------------------
def getInstancesStatus():
  sys.stdout.write("Searching instances status...\n")

  countInstancesActive = 0
  countInstancesNotActive = 0

  try:

    # Get account information
    account = client.get('/me')

    # Get projects
    projects = client.get('/cloud/project')

    for project in projects:

      countInstancesActiveProject = 0
      countInstancesNotActiveProject = 0

      # Get project info
      project_info = client.get('/cloud/project/'+project)

      # Get Instances from project
      instances = client.get('/cloud/project/'+project+'/instance')

      for instance in instances:

          if instance['status'] == 'ACTIVE':
            countInstancesActive = countInstancesActive + 1
            countInstancesActiveProject = countInstancesActiveProject + 1
          else:
            sys.stdout.write("- INSTANCE: {'project': '"+project_info['description']+", 'region': '"+instance['region']+"', 'name': '"+instance['name']+"', 'status': '"+instance['status']+"'\n")
            countInstancesNotActive = countInstancesNotActive + 1
            countInstancesNotActiveProject = countInstancesNotActiveProject + 1

      GaugeInstancesStatus.labels(account['nichandle'], project_info['description'], 'ACTIVE').set(countInstancesActiveProject)
      GaugeInstancesStatus.labels(account['nichandle'], project_info['description'], 'NOTACTIVE').set(countInstancesNotActiveProject)

    sys.stdout.write(str(countInstancesActive) + " instances active\n")
    sys.stdout.write(str(countInstancesNotActive) + " instances not active\n")
    GaugeInstancesStatus.labels(account['nichandle'], 'total', 'ACTIVE').set(countInstancesActive)
    GaugeInstancesStatus.labels(account['nichandle'], 'total', 'NOTACTIVE').set(countInstancesNotActive)

  except Exception as e:
    sys.stderr.write('error:'+str(e))

# -------------------------------------------------------
# Count instances hourly billing
# -------------------------------------------------------
def getInstancesHourlyBilling():
  sys.stdout.write("Searching hourly billing instances...\n")

  countInstances = 0

  try:

    # Get account information
    account = client.get('/me')

    # Get projects
    projects = client.get('/cloud/project')

    for project in projects:

      countInstancesProject = 0

      # Get project info
      project_info = client.get('/cloud/project/'+project)

      # Get Instances from project
      instances = client.get('/cloud/project/'+project+'/instance')

      for instance in instances:

          if instance['monthlyBilling'] == None:
            sys.stdout.write("- INSTANCE: {'project': '"+project_info['description']+", 'region': '"+instance['region']+"', 'name': '"+instance['name']+"'\n")
            countInstances = countInstances + 1
            countInstancesProject = countInstancesProject + 1

      GaugeInstancesHourlyBilling.labels(account['nichandle'], project_info['description']).set(countInstancesProject)

    sys.stdout.write(str(countInstances) + " instances hourly billing\n")
    GaugeInstancesHourlyBilling.labels(account['nichandle'], 'total').set(countInstances)

  except Exception as e:
    sys.stderr.write('error:'+str(e))

# -------------------------------------------------------
# Count Volumes not attached
# -------------------------------------------------------
def getVolumesNotAttached():
  sys.stdout.write("Searching not attached volumes...\n")

  countVolumes = 0

  try:

    # Get account information
    account = client.get('/me')

    # Get projects
    projects = client.get('/cloud/project')

    for project in projects:

      countVolumesProject = 0

      # Get project info
      project_info = client.get('/cloud/project/'+project)

      # Get Volumes form project
      volumes = client.get('/cloud/project/'+project+'/volume')

      for volume in volumes:

          if len(volume['attachedTo']) == 0:
            sys.stdout.write("- VOLUME: {'project': '"+project_info['description']+", 'region': '"+volume['region']+"', 'name': '"+volume['name']+"'\n")
            countVolumes = countVolumes + 1
            countVolumesProject = countVolumesProject + 1

      GaugeVolumesNotAttached.labels(account['nichandle'], project_info['description']).set(countVolumesProject)

    sys.stdout.write(str(countVolumes) + " volumes not attached found\n")
    GaugeVolumesNotAttached.labels(account['nichandle'], 'total').set(countVolumes)

  except Exception as e:
    sys.stderr.write('error:'+str(e))

# -------------------------------------------------------
# Count blocked IPs
# -------------------------------------------------------
def getBlockedIPs():
  sys.stdout.write("Searching blocked IPs...\n")

  countBlocked = 0

  try:

    # Get account information
    account = client.get('/me')

    # Get all IPs
    ips = client.get('/ip')

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
            if spamipinfo['state'] == "blockedForSpam":
              sys.stdout.write('- IP:'+spamip[0]+'\n')
              countBlocked = countBlocked + 1
        except ovh.exceptions.ResourceNotFoundError:
          continue

    sys.stdout.write(str(countBlocked) + " blocked IPs found\n")
    GaugeBlockedIPs.labels(account['nichandle']).set(countBlocked)

  except Exception as e:
    sys.stderr.write('error:'+str(e))

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():

  # Start up the server to expose the metrics.
  start_http_server(port)

  # Generate some requests.
  while True:
      getInstancesStatus()
      getInstancesHourlyBilling()
      getVolumesNotAttached()
      getBlockedIPs()
      getForecastCost()
      time.sleep(interval)

# -------------------------------------------------------
# RUN
# -------------------------------------------------------

# http port - default 9298
port = int(os.getenv('PORT', 9298))

# Refresh interval between collects in seconds - default 300
interval = int(os.getenv('INTERVAL', 300))

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
GaugeBlockedIPs = Gauge('ovh_spam_blocked_ip', 'Count blocked IPs due to spam', ['account'])
GaugeForecastCost = Gauge('ovh_forecast_cost', 'forecast cost', ['account', 'project', 'ressource'])
GaugeVolumesNotAttached = Gauge('ovh_volume_not_attached', 'Count volume not attached to an instance', ['account', 'project'])
GaugeInstancesHourlyBilling = Gauge('ovh_instance_hourly_billing', 'Count instances hourly billing', ['account', 'project'])
GaugeInstancesStatus = Gauge('ovh_instance_Status', 'Count instances by status', ['account', 'project', 'status'])

if __name__ == '__main__':
  main()
