ARG BUILD_FROM=ghcr.io/hassio-addons/base:13.0.0
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

ARG BUILD_ARCH=amd64

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Copy Python requirements file
COPY rootfs/usr/local/bin/scgi_server/src/requirements.txt /tmp/

# Setup base
# hadolint ignore=DL3003,DL3042
RUN \
    apk add --no-cache \
        #build-base \
        #libffi-dev \
        py3-wheel=0.38.4-r0 \
        python3-dev=3.10.9-r1 \
    \
    && apk add --no-cache \
        py3-bcrypt=4.0.1-r0 \
        py3-cryptography=38.0.3-r0 \
        py3-pip=22.3.1-r1 \
        python3=3.10.9-r1 \
    \
    && pip install -r /tmp/requirements.txt \
    \
    && apk del --no-cache

# Copy root filesystem
COPY rootfs /

RUN for file in /etc/services.d/*/*; do \
    dos2unix $file; \
    chmod a+xwr $file; \
    done

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
    org.opencontainers.image.vendor="Home Assistant Community Add-ons" \
    org.opencontainers.image.authors="Franck Nijhof <frenck@addons.community>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://addons.community" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}