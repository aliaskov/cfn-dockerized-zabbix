# My version of zabbix aws monitoring

Why is it unique?

Zabbix agent automatically connects to cloudwatch and discovers AWS services (EC, EC2, RDS, ASG, DynamoDB) and starts monitoring "out of the box". It's not perfect, templates require some tuning and adjustments.

Services:
1. DB
2. Zabbix server
3. Zabbix web interface
4. Zabbix agent with scripts, based on original zabbix/zabbix-agent alpine image

Contains 4 images:
1. mysql:5.7
2. zabbix/zabbix-server-mysql:latest
3. zabbix/zabbix-web-nginx-mysql:latest
4. aliaskov/aws-zabbix-agent:latest

Ports:
1. 3306/tcp for DB conections
2. 10051/tcp Zabbix checks
3. 8080/tcp For Web Interface

Mounts:
1. DB data files mysql_data/ on host are mounted on container's /var/lib/mysql
2. Custom py scripts  from agent_scripts/ are mounted on container's  /etc/zabbix/zabbix_scripts
3. Config files for scripts  from agent_conf/ are mounted on container's  /etc/zabbix/zabbix_agentd.d

AWS permissions:
1. Cloudwatch readonly
2. EC2 readonly
3. RDS readonly (if RDS monitoring is needed)
4. DynamoDB readonly (if DynamoDB monitoring is needed)
5. AmazonElastiCacheReadOnlyAccess  (if AmazonElastiCache monitoring is needed)

Usage

1. Use docker compose file to start stack.
 docker-compose -f zabbix-docker-compose.yml up -d

2. Import xml files (from templates dir) to zabbix web frontend, using web interface : Configuration - Templates - Import


Don't forget to delete all existing teplates, and disconnect zabbix server from default linux PASSIVE template.

![](https://github.com/aliaskov/dockerized-zabbix/raw/master/templates.png)
