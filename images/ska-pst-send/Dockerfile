ARG SEND_BUILDER=""
ARG SEND_RUNTIME=""

FROM $SEND_BUILDER as builder

FROM $SEND_RUNTIME
ENV DEBIAN_FRONTEND noninteractive
LABEL \
    author="Jesmigel A. Cantos <jesmigel.developer@gmail.com>" \
    description="This image includes the dependencies for building ska-pst-send" \
    license="BSD-3-Clause" \
    base="${SEND_BASE_IMAGE}" \
    org.skatelescope.team="PST Team" \
    org.skatelescope.version="0.0.6" \
    int.skao.application="ska-pst-send Builder"

# Copy across files that are used to help orchestrate container compositions
# and test execution sequences
ARG UID=1000
ARG GID=1000
ARG UNAME=pst

RUN groupadd -g $GID $UNAME  && \
    useradd -m -u $UID -g $GID -s /bin/bash $UNAME

WORKDIR /app

COPY images/ska-pst-send/pip.conf /etc/pip.conf

# Install common apt dependencies
ARG DEPENDENCIES_PATH=dependencies
ARG PKG_CLI_PAYLOAD=${DEPENDENCIES_PATH}/runtime.apt.txt

ENV PST_DSP_MOUNT=""

COPY ${PKG_CLI_PAYLOAD} ${PKG_CLI_PAYLOAD}
RUN stat ${PKG_CLI_PAYLOAD} \
    && apt-get update -y \
    && apt-get install --no-install-recommends -y $(cat ${PKG_CLI_PAYLOAD}) \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f ${PKG_CLI_PAYLOAD}

# Copy over STAT libraries
WORKDIR /usr/local
COPY --from=builder /usr/local/bin/ska_pst_stat* ./bin/
COPY --from=builder /usr/local/lib/libska_pst*.so ./lib/
COPY --from=builder /usr/local/lib/libpsr*.so* ./lib/
COPY --from=builder /usr/local/lib/libprotobuf*.so* ./lib/
COPY --from=builder /usr/local/lib/libgrpc*.so* ./lib/
COPY --from=builder /usr/local/lib/libabsl*.so* ./lib/
COPY --from=builder /usr/local/lib/libaddress_sorting.so* ./lib/
COPY --from=builder /usr/local/lib/libcrypto.so* ./lib/
COPY --from=builder /usr/local/lib/libgpr.so* ./lib/
COPY --from=builder /usr/local/lib/libre2.so* ./lib/
COPY --from=builder /usr/local/lib/libssl.so* ./lib/
COPY --from=builder /usr/local/lib/libupb.so* ./lib/
COPY --from=builder /usr/local/lib/libz.so* ./lib/

RUN ldconfig

RUN ska_pst_stat_file_proc -h \
    && ska_pst_stat_info -h

WORKDIR /app

# Install poetry as a binary
ENV POETRY_HOME=/opt/poetry
ARG POETRY_VERSION="1.3.2"

# Intermittent sSL connection error encountered
COPY install-poetry.py .
RUN python3 install-poetry.py --version ${POETRY_VERSION} \
    && ln -sfn /usr/bin/python3 /usr/bin/python \
    && ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry \
    && rm install-poetry.py

COPY --chown=${GID}:${UID} src/ /app/src/
COPY --chown=${GID}:${UID} pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --without dev

RUN mkdir -m777 -p /mnt/lfs

USER ${UNAME}

RUN sdp_transfer -h

CMD ["/bin/bash"]
