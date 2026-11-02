FROM jenkins/inbound-agent@sha256:9b078d6ef37444921ef266adb9ae2ff01fd85a0cdadb3ce657b2c5399bd52ea7

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

USER jenkins
