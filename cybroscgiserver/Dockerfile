# https://developers.home-assistant.io/docs/add-ons/configuration#add-on-dockerfile
ARG BUILD_FROM=ghcr.io/hassio-addons/base:17.0.1
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

ARG BUILD_ARCH=amd64

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy Python requirements file
COPY rootfs/usr/local/bin/scgi_server/requirements.txt /tmp/

# Setup base
# hadolint ignore=DL3003,DL3042,DL3018
RUN \
    apk add --no-cache \
        build-base \
        libffi-dev \
        py3-wheel \
        python3-dev \
    \
    && apk add --no-cache \
        py3-bcrypt \
        py3-cryptography \
        py3-pip \
        python3 \
    \
    && pip install iniparse==0.5 \
    && pip install crudini==0.9.5 \
    && pip install -r /tmp/requirements.txt

# Copy root filesystem
COPY rootfs /

# do post modifications
RUN mkdir /usr/local/bin/scgi_server/log \
    && touch /usr/local/bin/scgi_server/log/scgi.log \
    && ln -sf /dev/stdout /usr/local/bin/scgi_server/log/scgi.log

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Daniel Gangl <killer007@gmx.at>" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="Home Assistant Daniel's Add-ons" \
    org.opencontainers.image.authors="Daniel Gangl <killer007@gmx.at>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://addons.community" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}