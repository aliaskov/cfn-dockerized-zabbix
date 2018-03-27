FROM zabbix/zabbix-agent:latest
COPY zabbix_agent/zabbix_conf/ /etc/zabbix/zabbix_agentd.d
COPY zabbix_agent/zabbix_scripts/ /etc/zabbix/zabbix_scripts
USER root
RUN chown zabbix /etc/zabbix/zabbix_agentd.d
RUN chown zabbix /etc/zabbix/zabbix_scripts
RUN chmod -R a+x /etc/zabbix/zabbix_scripts/
USER zabbix
