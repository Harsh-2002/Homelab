FROM alpine:3.23@sha256:85fe1e81d6758c208f3e1eed4338a1997e19d4be002d4dd32d3100c9a8c010a0 AS download
ARG PB_VERSION=0.40.5
ARG PB_SHA256=1dbea1b01eb3dfe64953513859d01e759c96650c4e3264fa4eecd54b769382e4
ADD https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip /tmp/pb.zip
RUN echo "${PB_SHA256}  /tmp/pb.zip" | sha256sum -c - && unzip /tmp/pb.zip -d /pb

FROM alpine:3.23@sha256:85fe1e81d6758c208f3e1eed4338a1997e19d4be002d4dd32d3100c9a8c010a0
RUN apk add --no-cache ca-certificates && addgroup -g 10001 pocketbase && adduser -D -u 10001 -G pocketbase pocketbase
COPY --from=download /pb/pocketbase /usr/local/bin/pocketbase
USER 10001:10001
WORKDIR /pb
ENTRYPOINT ["pocketbase"]
CMD ["serve", "--http=0.0.0.0:8090", "--dir=/pb/pb_data", "--migrationsDir=/pb/pb_migrations", "--hooksDir=/pb/pb_hooks"]
