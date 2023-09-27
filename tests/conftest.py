from contextlib import closing
from http.client import HTTPConnection

import pytest


def _open_ipv4_ports():
    for line in open("/proc/net/tcp").readlines():
        bits = line.split(":", 3)
        if len(bits) != 4:
            continue
        port = bits[2].split(maxsplit=1)[0]
        yield int(port, 16)


def _ports_to_test(start_port=6000, max_delta=20):
    ports = list(sorted(_open_ipv4_ports()))
    for prev_port, port in zip([0] + ports[:-1], ports):
        delta = port - max(prev_port, start_port)
        if delta < 1:
            continue
        if delta > max_delta:
            break
        yield port


@pytest.fixture(params=_ports_to_test())
def port(request):
    yield request.param


@pytest.fixture
def addr(port):
    yield "localhost", port


@pytest.fixture
def conn(addr):
    with closing(HTTPConnection(*addr)) as conn:
        yield conn
