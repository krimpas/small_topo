FROM python:3.9.1-slim

WORKDIR /drone/src

ENV PROJECT_ROOT_DIR=/drone/src
ENV DATA_DIR=${PROJECT_ROOT_DIR}/data
ENV YML_DIR=${DATA_DIR}/yml
ENV INV_DIR=${DATA_DIR}/inv
ENV SCHEMA_DIR=${DATA_DIR}/schema/include.d
ENV VALID_DIR=${DATA_DIR}/schema
ENV J2_DIR=${DATA_DIR}/j2
ENV CONFIG_DIR=${DATA_DIR}/snapshots/configs
ENV NORNIR_CONFIG_DIR=${PROJECT_ROOT_DIR}/inv
ENV NORNIR_CONFIG_FILE=${PROJECT_ROOT_DIR}/config.yml
ENV CODE_DIR=${PROJECT_ROOT_DIR}/code
ENV CERBERUS_DIR=${CODE_DIR}/cerberus
ENV BATFISH_DIR=${CODE_DIR}/batfish
ENV SNAPSHOT_DIR=${DATA_DIR}/snapshot
ENV BATFISH_HOST=batfish
# Install dependencies:
COPY requirements.txt .
RUN pip install -r requirements.txt

