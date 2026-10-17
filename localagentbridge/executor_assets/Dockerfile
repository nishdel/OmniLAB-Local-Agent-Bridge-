# Build only after explicit setup approval; LAB never builds/pulls at dispatch.
# Supply an operator-verified base image digest and pin the resulting local image ID.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
USER root
COPY requirements.txt /opt/lab/requirements.txt
RUN python -m pip install --no-cache-dir -r /opt/lab/requirements.txt
COPY runner.py transport.py bounded.py /opt/lab/
ENTRYPOINT []
RUN mkdir -p /workspace /exchange /state /tmp/lab && chmod 0555 /workspace /opt/lab && chmod 0777 /exchange /state /tmp/lab
ENV HOME=/state PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TMPDIR=/tmp/lab
LABEL org.omnilab.sdk="1.53.0" org.omnilab.transport="readonly_tmpfs_v1" org.omnilab.commands="bounded_v3"
USER 10001:10001
WORKDIR /workspace
CMD ["python", "/opt/lab/transport.py", "supervise", "agent"]
