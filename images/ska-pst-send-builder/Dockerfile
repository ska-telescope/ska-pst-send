ARG SEND_BASE_IMAGE=""
ARG STAT_RUNTIME_IMAGE=""

FROM $STAT_RUNTIME_IMAGE as stat-runtime

FROM $SEND_BASE_IMAGE

ENV DEBIAN_FRONTEND noninteractive

LABEL \
    author="Jesmigel A. Cantos <jesmigel.developer@gmail.com>" \
    description="This image includes the dependencies for building ska-pst-send" \
    base="${SEND_BASE_IMAGE}" \
    org.skatelescope.team="PST Team" \
    org.skatelescope.version="0.0.7" \
    int.skao.application="ska-pst-send Builder"

WORKDIR /app

COPY images/ska-pst-send-builder/pip.conf /etc/pip.conf

# Install common apt dependencies
ARG DEPENDENCIES_PATH=dependencies
ARG PKG_CLI_PAYLOAD=${DEPENDENCIES_PATH}/base.apt.txt

COPY ${PKG_CLI_PAYLOAD} ${PKG_CLI_PAYLOAD}
RUN stat ${PKG_CLI_PAYLOAD} \
    && apt-get update -y \
    && apt-get install --no-install-recommends -y $(cat ${PKG_CLI_PAYLOAD}) \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f ${PKG_CLI_PAYLOAD}

# Copy over STAT libraries
WORKDIR /usr/local
COPY --from=stat-runtime /usr/local/bin/ska_pst_stat* ./bin/
COPY --from=stat-runtime /usr/local/lib/libska_pst*.so ./lib/
COPY --from=stat-runtime /usr/local/lib/libpsr*.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libprotobuf*.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libgrpc*.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libabsl*.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libaddress_sorting.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libcrypto.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libgpr.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libre2.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libssl.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libupb.so* ./lib/
COPY --from=stat-runtime /usr/local/lib/libz.so* ./lib/

RUN ldconfig

RUN ska_pst_stat_file_proc -h \
    && ska_pst_stat_info -h

WORKDIR /app

# Install poetry as a binary
ENV POETRY_HOME=/opt/poetry
ARG POETRY_VERSION="1.3.2"

# Intermittent sSL connection error encountered
# RUN curl -sSL https://install.python-poetry.org | python3 - --yes
COPY install-poetry.py .
RUN python3 install-poetry.py --version ${POETRY_VERSION} \
    && ln -sfn /usr/bin/python3 /usr/bin/python \
    && ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry

COPY src/ /app/src/
COPY tests/ /app/tests/
COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --with dev \
    && PYTHONPATH="/app/src" pytest tests

RUN sdp_transfer -h

CMD [ "bash" ]
