ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/ash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN \
    apk update && \
    apk add --no-cache \
        python3 \
        py3-pip && \
    pip3 install --upgrade pip && \
    pip3 install pysolarmanv5 requests websockets asyncws

# Copy data for add-on
COPY script.py /
COPY run.sh /
RUN chmod a+x /script.py /run.sh

# Start the shell script
CMD ["/run.sh"]
