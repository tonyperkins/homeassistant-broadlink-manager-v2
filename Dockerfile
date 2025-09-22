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
    curl

# Python requirements
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy data for add-on
COPY run.sh /
COPY app/ /app/

# Make run.sh executable
RUN chmod a+x /run.sh

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
    io.hass.version="1.0.0" \
    io.hass.url="https://github.com/yourusername/broadlink-manager-addon" \
    io.hass.maintainer="Your Name <your.email@example.com>"

CMD [ "/run.sh" ]
