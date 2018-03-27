FROM zabbix/zabbix-agent:latest
RUN apk add --update \
 python \
 py-pip
RUN pip install boto boto3 awscli \
 && rm -rf /var/cache/apk/*
