# Indifferent base image, just OS and GitAutoDeploy.
# Consumers should add configs, keys, users etc.
#
# People prefer different ways of configuring:
# volumes, ONBUILD instructions, secrets, configs, evironment vairables.
# This image doesn't have any proposals to let everyone do what they want.
FROM alpine:3.15
# Build context is expected to be the root of the git repository Git-Auto-Deploy.

RUN apk --no-cache --update add \
        python2 ca-certificates git openssh-client \
        && \
    python --version && which python && \
    wget https://bootstrap.pypa.io/pip/2.7/get-pip.py && \
    python get-pip.py && pip install --upgrade pip && rm get-pip.py && \
    rm -rf /var/cache/apk/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY gitautodeploy /app/gitautodeploy

WORKDIR /app
ENTRYPOINT ["/usr/bin/python", "-m", "gitautodeploy"]
