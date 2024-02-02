ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/ash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN \
    apk add --no-cache \
        python3 \
        py3-pip \
    && pip3 install pysolarmanv5 \
    && pip3 install requests \
    && pip3 install websockets \
    && pip3 install asyncio \
    && pip3 install asyncws

# Copy data for add-on
COPY script.py /
COPY run.sh /
RUN chmod a+x /script.py /run.sh

# Define an environment variable
ENV SUPERVISOR_TOKEN=${SUPERVISOR_TOKEN}

# Start the shell script
CMD [ "/run.sh" ]
