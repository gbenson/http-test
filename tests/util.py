class ResponseInterceptor:
    def __init__(self, sock):
        self._sock = sock
        self._read = []

    @property
    def response(self):
        return b"".join(self._read)

    def makefile(self, mode):
        return ResponseInterceptorFile(self, mode)

    def close(self):
        self._sock.close()


class ResponseInterceptorFile:
    def __init__(self, ri, mode):
        self._ri = ri
        self._fp = ri._sock.makefile(mode)

    def close(self):
        self._fp.close()

    def flush(self):
        self._fp.flush()

    def read(self, *args, **kwargs):
        data = self._fp.read(*args, **kwargs)
        self._ri._read.append(data)
        return data

    def readline(self, *args, **kwargs):
        data = self._fp.readline(*args, **kwargs)
        self._ri._read.append(data)
        return data
