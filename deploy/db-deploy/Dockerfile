FROM flyway/flyway:12.11.0-alpine

USER root
RUN apk add --no-cache bash python3 py3-pip postgresql-client jq
COPY deploy/db-deploy/sql /ops/sql
COPY deploy/db-deploy/deploy.sh /ops/deploy.sh

ENTRYPOINT [ "/ops/deploy.sh" ]