FROM zabbix/zabbix-agent:alpine-latest
RUN apk add --no-cache --virtual py-boto3
COPY --chown=zabbix:zabbix ./agent_conf /etc/zabbix/zabbix_agentd.d
COPY --chown=zabbix:zabbix ./agent_scripts /etc/zabbix/zabbix_scripts
