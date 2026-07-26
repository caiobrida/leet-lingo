FROM python:3.13-slim

RUN groupadd --system solution \
 && useradd --system --gid solution --no-create-home --shell /usr/sbin/nologin solution \
 && find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -exec chmod ug-s {} +

COPY harness /opt/harness

ENV PYTHONPATH=/opt

ENTRYPOINT ["python", "-m", "harness"]
