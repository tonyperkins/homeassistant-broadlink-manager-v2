ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    curl \
    jq \
    bash

# Python requirements
# Cache bust: 2025-10-10-v2
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Copy data for add-on
COPY run.sh /
COPY app/ /app/

# Fix line endings and make run.sh executable
RUN sed -i 's/\r$//' /run.sh && chmod a+x /run.sh

# Set working directory
WORKDIR /app

# Expose the web interface port
EXPOSE 8099

# Labels
LABEL \
    io.hass.name="Broadlink Manager" \
    io.hass.description="A Home Assistant add-on for managing Broadlink devices with web interface" \
    io.hass.arch="armhf|aarch64|amd64|armv7|i386" \
    io.hass.type="addon" \
    io.hass.version="1.10.12" \
    io.hass.url="https://github.com/tonyperkins/homeassistant-broadlink-manager" \
    io.hass.maintainer="Tony Perkins"

CMD [ "/run.sh" ]
