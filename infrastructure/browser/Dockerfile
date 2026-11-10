FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 \
    HOME=/state XDG_CONFIG_HOME=/state/config XDG_CACHE_HOME=/state/cache \
    ANONYMIZED_TELEMETRY=false BROWSER_USE_TELEMETRY=false
RUN apt-get update && apt-get install -y --no-install-recommends chromium ca-certificates tini fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && pip install 'browser-use==1.0.0' \
    && useradd --uid 1000 --create-home browser
COPY --chmod=644 runtime.py /opt/browser/runtime.py
COPY --chmod=644 task.py /opt/browser/task.py
COPY --chmod=644 requirements.lock /opt/browser/requirements.lock
RUN pip install --no-deps -r /opt/browser/requirements.lock
RUN chmod 755 /opt /opt/browser && chmod 644 /opt/browser/*.py
USER 1000:1000
WORKDIR /state
ENTRYPOINT ["/usr/bin/tini", "-s", "--"]
CMD ["python", "/opt/browser/runtime.py", "serve"]
