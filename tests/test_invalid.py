from http.client import _CS_IDLE, _CS_REQ_SENT, _UNKNOWN

import pytest

from .util import ResponseInterceptor


def test_invalid_method(conn):
    conn.debuglevel = 10
    conn.connect()
    assert conn._HTTPConnection__state == _CS_IDLE

    req = b'G"T / HTTP/1.1\r\nHost: localhost\r\n\r\n'
    n = conn.sock.send(req)
    assert n == len(req)

    conn._HTTPConnection__state = _CS_REQ_SENT
    r = conn.getresponse()

    server_header = r.headers.get("Server", "")
    is_python = "Python" in server_header

    if is_python:
        assert r.status == 501
        return

    assert r.status == 400
    if r.reason == "Bad Request":
        return

    is_tomcat = not server_header and b"Tomcat" in r.read()
    assert is_tomcat and r.reason == ""


@pytest.mark.parametrize(
    "request_line",
    (
     b'GET / HTTP/1',
     b'GET / HTTP/2',
     b'GET / HTTP/1,1',
     b'GET / HTTP/a.1',
     b'GET / HTTP/1.a',
     ))
def test_invalid_protocol_version(conn, request_line, monkeypatch):
    req = request_line + b"\r\nHost: localhost\r\n\r\n"

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
        assert ri.response == b"<!DOCTYPE HTML>\n"
        return

    server_header = r.headers.get("Server", "")
    is_python = "Python" in server_header
    is_nginx = "nginx" in server_header
    is_tomcat = not server_header and b"Tomcat" in r.read()

    if r.status == 400:
        assert r.reason == "" if is_tomcat else "Bad Request"
        return

    assert r.status == 505

    if request_line == b"GET / HTTP/1":
        assert is_tomcat
        assert r.reason == ""
        return

    assert request_line == b"GET / HTTP/2"
    assert is_nginx or is_tomcat
    assert r.reason == "" if is_tomcat else "HTTP Version Not Supported"
