FROM timescale/timescaledb-ha:pg13-latest
ENV POSTGRES_USER docker
ENV POSTGRES_PASSWORD password
ENV POSTGRES_DB starter_kit
COPY scripts/* /docker-entrypoint-initdb.d/
COPY data/* ./