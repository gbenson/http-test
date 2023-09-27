from http.client import _CS_IDLE, _CS_REQ_SENT, _UNKNOWN

import pytest

from .util import ResponseInterceptor


@pytest.mark.parametrize(
    "method,expect_status",
    (("PATCH", 405),
     ("get", 501),
     ("G'T", 501), # actually valid!
     ))
def test_unsupported_method(conn, method, expect_status):
    req = (method + " / HTTP/1.1\r\nHost: localhost\r\n\r\n").encode()

    conn.debuglevel = 10
    conn.connect()
    assert conn._HTTPConnection__state == _CS_IDLE

    n = conn.sock.send(req)
    assert n == len(req)

    conn._HTTPConnection__state = _CS_REQ_SENT
    r = conn.getresponse()

    server_header = r.headers.get("Server", "")
    is_nginx = "nginx" in server_header
    is_python = "Python" in server_header
    is_golang = "golang" in server_header

    body = r.read()
    is_tomcat = not server_header and b"Tomcat" in body

    if is_nginx and expect_status == 501:
        expect_status = 400
    if is_tomcat:
        expect_status = 404
    if is_python and expect_status == 405:
        expect_status = 501
    if is_golang:
        expect_status = 200

    assert r.status == expect_status


@pytest.mark.parametrize(
    "req, expect_status",
    ((b"GET / HTTP/1.2\r\nHost: localhost\r\n\r\n", 200),
     (b"PRI * HTTP/2.0\r\n\r\n",  400),  # see golang Request.isH2Upgrade()
     (b"GET / HTTP/4\r\nHost: localhost\r\n\r\n", 400),
     ))
def test_unsupported_protocol_version(conn, req, expect_status, monkeypatch):
    conn.debuglevel = 10
    conn.connect()
    assert conn._HTTPConnection__state == _CS_IDLE

    n = conn.sock.send(req)
    assert n == len(req)

    conn._HTTPConnection__state = _CS_REQ_SENT
    ri = ResponseInterceptor(conn.sock)
    exc = None
    with monkeypatch.context() as m:
        m.setattr(conn, "sock", ri)
        try:
            r = conn.getresponse()
        except Exception as _exc:
            exc = _exc

    if exc is not None:
        # Python SimpleHTTPServer
        assert not b"HTTP/1" in req
        assert ri.response == b"<!DOCTYPE HTML>\n"
        return

    body = r.read()
    print(f"body: {body!r}"[:80])
    if not body:
        # golang
        assert req.startswith(b"PRI * HTTP/2.0")
        assert r.status == 400
        assert r.reason == "Bad Request"

    server_header = r.headers.get("Server", "")
    is_python = "Python" in server_header
    is_tomcat = b"Tomcat" in body

    assert r.version == 10 if is_python else 11
    assert r.chunked is False
    assert r.chunk_left is _UNKNOWN
    assert r.will_close or expect_status == 200 or is_tomcat

    if r.status == 505:
        assert r.reason == "" if is_tomcat else "HTTP Version Not Supported"
        return

    if is_tomcat:
        expect_status = 400
    elif expect_status == 200 and "Location" in r.headers:
        expect_status = 302

    assert r.status == expect_status
    assert r.reason == {
        200: "OK",
        302: "Found",
        400: "" if is_tomcat else "Bad Request",
        }.get(r.status)


def test_unsupported_expectation(conn):
    conn.connect()
    assert conn._HTTPConnection__state == _CS_IDLE

    req = b"GET / HTTP/1.1\r\nHost: localhost\r\nExpect: chonking\r\n\r\n"
    n = conn.sock.send(req)
    assert n == len(req)

    conn._HTTPConnection__state = _CS_REQ_SENT
    r = conn.getresponse()

    body = r.read()

    server_header = r.headers.get("Server", "")
    is_tomcat = not server_header and b"Tomcat" in body

    if r.status == 417:
        assert r.reason == "" if is_tomcat else "Expectation Failed"
        return

    assert r.status == 200
    is_python = "Python" in server_header
    is_nginx = "nginx" in server_header
    assert is_python or is_nginx


def test_unsupported_transfer_encoding(conn):
    conn.connect()
    assert conn._HTTPConnection__state == _CS_IDLE

    req = b"GET / HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chonked\r\n\r\n"
    n = conn.sock.send(req)
    assert n == len(req)

    conn._HTTPConnection__state = _CS_REQ_SENT
    r = conn.getresponse()

    body = r.read()
    assert len(body) > 27

    server_header = r.headers.get("Server", "")
    is_tomcat = not server_header and b"Tomcat" in body

    if r.status == 501:
        assert r.reason == "" if is_tomcat else "Not Implemented"
        return

    is_python = "Python" in server_header
    assert r.status == 200 if is_python else 400
    assert r.reason == {
        200: "OK",
        400: "Bad Request",
        }.get(r.status)
