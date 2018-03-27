#!/usr/bin/env python

import argparse
import boto3
import boto.ec2.elb
import boto.elasticache
from boto.ec2.cloudwatch import CloudWatchConnection
from boto.ec2 import *
import boto.ec2.autoscale
import boto.rds2
import boto.dynamodb
import datetime
import os, time
import json
#import ec2metadata
import signal
#amazon uses UTC at cloudwatch
os.environ['TZ'] = 'UTC'
time.tzset()

# Regions to scan for discovery
REGIONS = boto.ec2.regions()

discovery_regions=[]
for region in REGIONS:
        discovery_regions.append(region.name)

parser = argparse.ArgumentParser(description='Zabbix CloudWatch client')
parser.add_argument('-r', '--region', dest='region', default='us-west-1', help='AWS region')
parser.add_argument('-d', '--dimension', dest='dimension', default=None, help='Cloudwatch Dimension')
parser.add_argument('-n', '--namespace', dest='namespace', default='AWS/EC2', help='Cloudwatch Namespace')
parser.add_argument('-m', '--metric', dest='metric', default='NetworkOut', help='Cloudwatch Metric')
parser.add_argument('-s', '--statistic', dest='statistic', default='Sum', help='Cloudwatch Statistic')
parser.add_argument('-i', '--interval', dest='interval', type=int,default=60, help='Interval')
parser.add_argument('-D', '--discovery', dest='discovery', choices=['ELB','ALB', 'RDS', 'ASG','ElastiCache','DynamoDB'], help='Run Discovery')
parser.add_argument('-l', '--elb', dest='elb', help='ELB to discover instances for')
parser.add_argument('-v', '--verbose', action='count', dest='verbose')
args = parser.parse_args()

if args.namespace == 'ELB':
  args.namespace = 'AWS/ELB'
  dimension = {'LoadBalancerName': args.dimension}
elif args.namespace == 'RDS':
  args.namespace = 'AWS/RDS'
  dimension = {'DBInstanceIdentifier': args.dimension}
elif args.namespace == 'ALB':
  args.namespace = 'AWS/ApplicationELB'
  dimension = {'LoadBalancer': args.dimension}
elif args.namespace == 'ASG':
  args.namespace = 'AWS/AutoScaling'
  dimension = {'AutoScalingGroupName': args.dimension}
elif args.namespace == 'DynamoDB':
  args.namespace = 'AWS/DynamoDB'
  dimension = {'TableName': args.dimension}
elif args.namespace == 'ElastiCache':
  args.namespace = 'AWS/ElastiCache'
  dimension = args.dimension.split(',')
  dimension = {'CacheClusterId': dimension[0], 'CacheNodeId': dimension[1]}
else:
  dimension = args.dimension

# Define handler and exception for timeout
timeout = 3
def handler(signum, frame):
	raise Exception('Connection Timeout')
signal.signal(signal.SIGALRM, handler)

def discovery():
  if 'ELB' in args.discovery:
    ELBRetData = { "data": [ ] }
    for region in discovery_regions:
       try:
         signal.alarm(timeout)
         conn = boto.ec2.elb.connect_to_region(region)
         elbs = conn.get_all_load_balancers()
       except:
         continue
       for elb in elbs:
         ELBRetData['data'].append(
           { '{#LOADBALANCERNAME}': elb.name, '{#ELBREGION}' : region }
         )
    print json.dumps(ELBRetData, indent=4)
  if 'ALB' in args.discovery:
    ALBRetData = { "data": [ ] }
    for region in discovery_regions:
       try:
         signal.alarm(timeout)
         conn = boto3.client('elbv2',region_name=region)
         albs = conn.describe_load_balancers()
       except:
         continue
       tempappname=''
       finaapplname=''
       for alb in albs['LoadBalancers']:
           tempappname=alb['LoadBalancerArn'].split('/')
           finaapplname=tempappname[1]+'/'+tempappname[2]+'/'+tempappname[3]
           ALBRetData['data'].append( { '{#LOADBALANCERNAME}': alb['LoadBalancerName'], '{#ALBREGION}' : region,'{#APPLOADBALANCERNAME}' : finaapplname })
    print json.dumps(ALBRetData, indent=4)

  elif 'RDS' in args.discovery:
    RDSRetData = { "data": [ ] }
    for region in discovery_regions:
      try:
        signal.alarm(timeout)
        conn = boto.rds2.connect_to_region(region)
        rdss = conn.describe_db_instances()
      except:
        continue
      for rds in rdss['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']:
  	RDSRetData['data'].append(
  	 { '{#RDSINSTANCEID}': rds['DBInstanceIdentifier'], '{#RDSREGION}' : region }
  	)
    print json.dumps(RDSRetData, indent=4)

  elif 'ASG' in args.discovery:
    ASGRetData = { "data": [ ] }
    for region in discovery_regions:
      try:
        signal.alarm(timeout)
        conn = boto.ec2.autoscale.connect_to_region(region)
        asgs = conn.get_all_groups()
      except:
        continue
      for asg in asgs:
  	ASGRetData['data'].append(
  	 { '{#ASGNAME}': asg.name, '{#ASGREGION}' : region }
  	)
    print json.dumps(ASGRetData, indent=4)

  elif 'DynamoDB' in args.discovery:
    DDBRetData = { "data": [ ] }
    for region in discovery_regions:
      try:
        signal.alarm(timeout)
        conn = boto.dynamodb.connect_to_region(region)
        ddbs = conn.list_tables()
      except:
        continue
      for ddb in ddbs:
  	DDBRetData['data'].append(
  	 { '{#DDBTABLE}': ddb, '{#REGION}' : region }
  	)
    print json.dumps(DDBRetData, indent=4)

  elif 'ElastiCache' in args.discovery:
    ElastiCacheRetData = { "data": [ ] }
    for region in discovery_regions:
      try:
        signal.alarm(timeout)
	conn=boto.elasticache.connect_to_region(region)
	cacheClusters=conn.describe_cache_clusters(show_cache_node_info=True)['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters']
      except:
        continue
      for cluster in cacheClusters:
        for node in cluster['CacheNodes']:
          ElastiCacheRetData['data'].append(
           { '{#CACHENAME}': cluster['CacheClusterId'], '{#CACHEREGION}' : region, '{#CACHENODEID}' : node['CacheNodeId']}
          )
    print json.dumps(ElastiCacheRetData, indent=4)
  return

def getASGMetric():
	try:
          signal.alarm(timeout)
          conn = boto.ec2.autoscale.connect_to_region(args.region)
        except:
          sys.exit(0)

	asg = conn.get_all_groups(names=[args.dimension])

	if str(args.metric) == 'GroupDesiredCapacity':
	  print asg[0].desired_capacity
	if str(args.metric) == 'GroupMaxSize':
	  print asg[0].max_size
	if str(args.metric) == 'GroupMinSize':
	  print asg[0].min_size

	if any(metric == args.metric for metric in ('GroupTotalInstances', 'GroupInServiceInstances', 'GroupUnHealthyInstances')):
	  asg_instances = conn.get_all_autoscaling_instances()
	  asgInstanceCount = 0
	  ASGInstances = []
	  for asg_instance in asg_instances:
	    if str(asg_instance.group_name) == args.dimension:
	      asgInstanceCount += 1
              ASGInstances.append(asg_instance)
	  if str(args.metric) == 'GroupTotalInstances':
	    print asgInstanceCount

	if any(metric == args.metric for metric in ('GroupInServiceInstances','GroupUnHealthyInstances')):
	  if str(args.metric) == 'GroupInServiceInstances':
	    inServiceCount = 0
	    if asgInstanceCount > 0:
	      for ASGInstance in ASGInstances:
	    	if ASGInstance.lifecycle_state == 'InService':
	    		inServiceCount += 1
	    print inServiceCount

	  elif str(args.metric) == 'GroupUnHealthyInstances':
	    unHealthyCount = 0
	    if asgInstanceCount > 0:
	      for ASGInstance in ASGInstances:
	    	if ASGInstance.health_status != 'HEALTHY':
	    		unHealthyCount += 1
	    print unHealthyCount

def getCloudWatchMetric():
  end_time = datetime.datetime.now()
  # adding 65 seconds due amazon caracteristic
  end_time = end_time - datetime.timedelta(seconds=65)
  start_time = end_time - datetime.timedelta(seconds=args.interval)

  if args.verbose:
    debug=args.verbose
  else:
    debug=0
  regions = boto.ec2.cloudwatch.regions()
  for reg in regions:
    if reg.name == args.region:
      cloudwatch = CloudWatchConnection(is_secure=True, debug=debug, region=reg)
  cloudwatch_result = None

  # Check if the metric has collected statistics. If it does not, say so
  metricsList = cloudwatch.list_metrics(dimensions=dimension, namespace=args.namespace)
  metricTest='Metric:'+args.metric
  strMetricsList=[]
  for item in metricsList:
    strMetricsList.append(str(item))
  if metricTest in strMetricsList:
    # Specify the application load balancer as follows: app/load-balancer-name/1234567890123456 (the final portion of the load balancer ARN)
    #tested metrics for ALB: TargetResponseTime(Average),RequestCount(Sum),ActiveConnectionCount(Sum),NewConnectionCount(Sum),HTTPCode_Target_4XX_Count(Sum),HTTPCode_Target_5XX_Count(Sum),HealthyHostCount(Average)
    cloudwatch_result = cloudwatch.get_metric_statistics(args.interval, start_time, end_time, args.metric, args.namespace, statistics=args.statistic, dimensions=dimension)
    if len(cloudwatch_result)>0:
      cloudwatch_result = cloudwatch_result[0]
      if len(cloudwatch_result) > 0:
          if len(repr(cloudwatch_result[args.statistic])) > 6:
              cloudwatch_result = long(cloudwatch_result[args.statistic])
          else:
              cloudwatch_result = float(cloudwatch_result[args.statistic])
    else:
      # Assuming value is 0 if AWS returned empty list
      cloudwatch_result = 0
    print  cloudwatch_result
  else:
    print 'Unsupported Metric'
  return

if args.discovery:
	discovery()
elif args.namespace == 'AWS/AutoScaling':
	getASGMetric()
else:
	getCloudWatchMetric()

