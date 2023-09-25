from contextlib import closing
from http.client import HTTPConnection

import pytest


@pytest.fixture(params=list(range(6001, 6006)))
def port(request):
    yield request.param


@pytest.fixture
def addr(port):
    yield "localhost", port


@pytest.fixture
def conn(addr):
    with closing(HTTPConnection(*addr)) as conn:
        yield conn
