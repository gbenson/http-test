from http.client import _CS_IDLE, _CS_REQ_SENT, _UNKNOWN

import pytest

from .util import ResponseInterceptor


@pytest.mark.parametrize(
    "req",
    (b" GET / HTTP/1.1",
     b"GET  / HTTP/1.1",
     b"GET /  HTTP/1.1",
     b"GET / HTTP/1.1 ",

     b"\tGET / HTTP/1.1",
     b"GET\t/ HTTP/1.1",
     b"GET\t / HTTP/1.1",
     b"GET \t/ HTTP/1.1",
     b"GET /\tHTTP/1.1",
     b"GET /\t HTTP/1.1",
     b"GET / \tHTTP/1.1",
     b"GET / HTTP/1.1\t",

     b"GET / HTTP /1.1",
     b"GET / HTTP/ 1.1",
     b"GET / HTTP/1 .1",
     b"GET / HTTP/1. 1",
     b"GET / HTTP\t/1.1",
     b"GET / HTTP/\t1.1",
     b"GET / HTTP/1\t.1",
     b"GET / HTTP/1.\t1",
     ))
def test_request_line_whitespace(conn, req, monkeypatch):
    req += b"\r\nHost: localhost\r\n\r\n"

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
        assert not b"HTTP/1.1" in req
        assert ri.response == b"<!DOCTYPE HTML>\n"
        return

    server_header = r.headers.get("Server", "")
    is_python = "Python" in server_header
    is_nginx = "nginx" in server_header
    if is_python or (is_nginx
                     and b"\t" not in req
                     and b"HTTP/1.1" in req
                     and req.lstrip() == req):
        assert r.status == 200
        return

    body = r.read()
    is_tomcat = not server_header and b"Tomcat" in body
    if is_tomcat and b"HTTP/1.1" in req:
        rl = req.split(b"\r", 1)[0]
        if rl.strip() == rl:
            assert r.status == 404
            return

    assert r.status == 400
