FROM python:3.12.12-alpine3.22

ARG BUILD_VERSION=0.1.0
ARG BUILD_ARCH=aarch64
LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/S1146468/Adaptive-Heating-Controller"

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/adaptive-heating-controller
COPY app ./app
COPY run.sh /run.sh
RUN chmod 0555 /run.sh
STOPSIGNAL SIGTERM
ENTRYPOINT ["/run.sh"]
