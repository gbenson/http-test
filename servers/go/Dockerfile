FROM golang:1.21-alpine as base
WORKDIR /srv

FROM base as builder
COPY go.mod main.go .
RUN go build -o server

FROM base
COPY --from=builder /srv/server /srv
EXPOSE 80
CMD ["/srv/server"]
