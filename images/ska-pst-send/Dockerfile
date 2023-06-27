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
    org.skatelescope.version="0.0.0" \
    int.skao.application="ska-pst-send Builder"
# ska-pst-send runtime artefacts
# install minimum required dependencies
# clean package manager(s)

# Copy across files that are used to help orchestrate container compositions
# and test execution sequences
ARG UID=1000
ARG GID=1000
ARG UNAME=pst

RUN groupadd -g $GID $UNAME  && \
    useradd -m -u $UID -g $GID -s /bin/bash $UNAME

# Add steps for runtime tests

CMD ["/bin/bash"]
