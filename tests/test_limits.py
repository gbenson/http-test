from http.client import _CS_IDLE, _CS_REQ_SENT, _UNKNOWN

import pytest


def test_huge_method(conn):
    conn.connect()
    assert conn._HTTPConnection__state == _CS_IDLE

    chunk = b"G" * (1<<10)
    total = 0
    for _ in range(20<<10):
        try:
            n = conn.sock.send(chunk)
        except Exception as e:
            print("caught", e)
            break
        total += n
        if n < len(chunk):
            break
    print("sent", total, "bytes")

    conn._HTTPConnection__state = _CS_REQ_SENT
    r = conn.getresponse()

    server_header = r.headers.get("Server", "")
    is_nginx = "nginx" in server_header
    is_python = "Python" in server_header

    body = r.read()
    assert len(body) > 34

    is_golang = (
        not server_header
        and body == b"431 Request Header Fields Too Large"
    )
    is_tomcat = b"Tomcat" in body

    assert r.version == 10 if is_python else 11
    assert r.status == (400 if is_tomcat else 431 if is_golang else 414)
    assert r.reason == {
        400: "" if is_tomcat else "Bad Request",
        414: "Request-URI Too Large" if is_nginx else "Request-URI Too Long",
        431: "Request Header Fields Too Large",
        }.get(r.status)
    assert r.chunked is False
    assert r.chunk_left is _UNKNOWN
    if is_golang:
        assert r.length is None
    else:
        assert r.length == 0
    assert r.will_close
