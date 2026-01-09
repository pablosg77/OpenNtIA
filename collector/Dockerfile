# Use official Alpine release
FROM telegraf:latest


# Change working dir
WORKDIR /telegraf

# Update apt and install python3, python3-pysnmp4
RUN apt-get update && apt-get install -y python3 python3-requests libxslt1-dev libssl-dev libffi-dev python3-lxml libxml2-dev libxslt-dev python-dev-is-python3 python3-pip

RUN pip3 install junos-eznc --break-system-packages
RUN pip3 install pandas --break-system-packages
RUN pip3 install lxml --break-system-packages

# Expose ports
EXPOSE 8125/udp 8092/udp 8094

# Set entrypoint and cmd
ENTRYPOINT ["/entrypoint.sh"]
CMD ["telegraf"]
