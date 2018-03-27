#!/usr/bin/python2.7

from pprint import pprint
import argparse
import boto.ec2
import sys
import json
import signal

# Define and initialize global variables and constants
#constants
#REGIONS = ['us-east-1','us-west-2','us-west-1','eu-west-1','eu-central-1','ap-southeast-1','ap-southeast-2','ap-northeast-1','sa-east-1']
#REGIONS = ['us-east-1']
FULL_REGIONS = boto.ec2.regions()
RUNNING = "running"
STOPPED = "stopped"
TERMINATED = "terminated"
EVENTCOMPLETED = 'Completed'
#global variables
totals = {}
instances_details = {}

REGIONS=[]
for region in FULL_REGIONS:
	REGIONS.append(region.name)

# Parse command line arguments
CHOICES=['all','total','running','ok','fail','faildetails','sysok','sysfail','sysfaildetails','stopped','terminated','completed','scheduled','scheduleddetails']
parser = argparse.ArgumentParser(description='ec2 summary')
parser.add_argument('-m', '--metric', dest='metric', choices=CHOICES, default=None, help='Available metrics to choose from')
parser.add_argument('-r', '--region', dest='region', choices=REGIONS, default=None, help='Available regions to choose from')
parser.add_argument('-d', '--discovery', action='count', dest='discovery', help='Run Discovery')
parser.add_argument('-v', '--verbose', action='count', dest='verbose')
args = parser.parse_args()

# Define handler and exception for timeout
timeout = 3
def handler(signum, frame):
	raise Exception('Connection Timeout')
signal.signal(signal.SIGALRM, handler)

# If discover, find running instances
if args.discovery > 0:
  args.metric = 'running'

DiscoveryData = { "data": [ ] }

try:
   if args.region:
	REGIONS=[args.region]
except:
   pass

for region in REGIONS:
	totals["total_instances"] = 0
	totals["running_instances"] = 0
	totals["instances_status_ok"] = 0
	totals["instances_status_fail"] = 0
	totals["instances_system_status_ok"] = 0
	totals["instances_system_status_fail"] = 0
	totals["stopped_instances"] = 0
	totals["terminated_instances"] = 0
	totals["instances_scheduled_completed_events"] = 0
	totals["instances_scheduled_events"] = 0

	try:
		signal.alarm(timeout)
		conn = boto.ec2.connect_to_region(region)
		#get statuses
		instance_statuses = conn.get_all_instance_status()
		#get all instances details
		all_instances = conn.get_all_instances()
	except:
		continue

	#get instances state
	if any(metric == args.metric for metric in ('all', 'total', 'running', 'terminated', 'stopped')):
		for instance in all_instances:
			for instance_id in instance.instances:
				instance_state = str(instance_id._state)
				totals["total_instances"] += 1
				if RUNNING in instance_state:
					totals["running_instances"] +=1
				elif STOPPED in instance_state:
					totals["stopped_instances"] +=1
				elif TERMINATED in instance_state:
					totals["terminated_instances"] +=1
	# Add region to discovery if running instances in that region
	if totals["running_instances"] >= 1:
		DiscoveryData['data'].append(
			{ '{#REGION}': region})
	#get instances status and system status
	if any(metric == args.metric for metric in ('all','ok', 'fail', 'sysok', 'sysfail','completed','scheduled','scheduleddetails','sysfaildetails','faildetails')):
		for instance in instance_statuses:
			system_status = str(instance.system_status)
			instance_status = str(instance.instance_status)
			if 'ok' in instance_status:
				totals["instances_status_ok"] +=1
			else:
				totals["instances_status_fail"] +=1
				instances_details["instance_status_error"].append(instance)
			if 'ok' in system_status:
				totals["instances_system_status_ok"] +=1
			else:
				totals["instances_system_status_fail"] +=1
				instances_details["instance_system_status_error"].append(instance)
			#check for instance events
			if instance.events:
				instances_details['events']={}
				instances_details['events'][instance.id]={}
				for event in instance.events:
					instances_details['events'][instance.id]['code'] = str(event.code)
					instances_details['events'][instance.id]['description'] = str(event.description)
					if EVENTCOMPLETED in instances_details['events'][instance.id]['description']:
						totals["instances_scheduled_completed_events"] +=1
					else:
						totals["instances_scheduled_events"] +=1

# Print totals values
if args.metric == 'total' or args.metric == 'all':
	print totals["total_instances"]
if args.metric == 'running' or args.metric == 'all':
	# if in discovery, return region
	if args.discovery > 0:
		print json.dumps(DiscoveryData, indent=4)
	else:
		print totals["running_instances"]
if args.metric == 'stopped' or args.metric == 'all':
	print totals["stopped_instances"]
if args.metric == 'terminated' or args.metric == 'all':
	print totals["terminated_instances"]
if args.metric == 'ok' or args.metric == 'all':
	print totals["instances_status_ok"]
if args.metric == 'fail' or args.metric == 'all':
	print totals["instances_status_fail"]
if args.metric == 'faildetails' or args.metric == 'all':
	if "instance_status_error" in instances_details:
		for item in instances_details["instance_status_error"]:
			pprint(item.encode(ascii))
if args.metric == 'sysok' or args.metric == 'all':
	print totals["instances_system_status_ok"]
if args.metric == 'sysfail' or args.metric == 'all':
	print totals["instances_status_fail"]
if args.metric == 'failsysdetails' or args.metric == 'all':
	if "instance_system_status_error" in instances_details:
		for item in instances_details["instance_system_status_error"]:
			pprint(item.encode(ascii))
if args.metric == 'scheduled' or args.metric == 'all':
	print totals["instances_scheduled_events"]
if args.metric == 'scheduleddetails' or args.metric == 'all':
	if "events" in instances_details:
		for instance in instances_details["events"]:
			print "instance id: " + instance
			print "instance event code: " + instances_details['events'][instance]['code']
#			pprint("instance event code: %s" % instances_details['events'][instance]['code'])
			print "instance event description: " + instances_details['events'][instance]['description']
#			pprint("instance event description: %s" % instances_details['events'][instance]['description'])
if args.metric == 'completed' or args.metric == 'all':
	print totals["instances_scheduled_completed_events"]
