FROM zabbix/zabbix-agent:centos-3.4-latest
RUN yum -y install epel-release
RUN yum -y install python-pip && yum clean all
RUN pip install  awscli boto




#FROM zabbix/zabbix-agent:latest
#RUN apk add --update \
# python \
# py-pip
#RUN pip install boto boto3 awscli \
# && rm -rf /var/cache/apk/*
