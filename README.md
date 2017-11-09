# docker compose file for zabbix stack

Services:
1. DB
2. Zabbix server
3. Zabbix web interface

Contains 3 images:
1. mysql:5.7
2. zabbix/zabbix-server-mysql:latest
3. zabbix/zabbix-web-nginx-mysql:latest

Ports:
1. 3306/tcp for DB conections
2. 10051/tcp Zabbix checks
3. 8080/tcp For Web Interface

Mounts:
1. DB data files mysql_data/ on host mounted on container's /var/lib/mysql

Usage
2. docker-compose -f zabbix-docker-compose.yml up -d
