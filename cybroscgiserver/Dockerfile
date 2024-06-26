# https://developers.home-assistant.io/docs/add-ons/configuration#add-on-dockerfile
ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.7
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

ARG BUILD_ARCH=amd64

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy Python requirements file
COPY rootfs/usr/local/bin/scgi_server/src/requirements.txt /tmp/

# Setup base
# hadolint ignore=DL3003,DL3042,DL3018
RUN \
    apk add --no-cache --virtual .build-dependencies \
        build-base=0.5-r3 \
        libffi-dev=3.4.4-r3 \
        py3-wheel=0.42.0-r0 \
        python3-dev=3.11.8-r0 \
    \
    && apk add --no-cache \
        py3-bcrypt=4.1.1-r0 \
        py3-cryptography=41.0.7-r0 \
        py3-pip=23.3.1-r0 \
        python3=3.11.8-r0 \
    \
    && pip install -r /tmp/requirements.txt \
    \
    && find /usr \
        \( -type d -a -name test -o -name tests -o -name '__pycache__' \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    \
    && apk del --no-cache --purge .build-dependencies

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