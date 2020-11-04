import socket
from typing import Callable, Dict, List, Optional

STATUS_CODES: Dict[int, str] = {
    200: 'OK',
    404: 'Not Found',
    501: 'Not Implemented'
}

HTTP_METHODS: List[str] = ['GET']


class TCPServer:

    def __init__(self, host: str = '127.0.0.1', port: int = 8000):
        self.host: str = host
        self.port: int = port

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(5)

            print(f'Listening at: {s.getsockname()}')

            while True:
                conn, addr = s.accept()
                data = conn.recv(1024)
                response: bytes = self.handle_request(data)
                conn.sendall(response)
                conn.close()

    def handle_request(self, data: bytes) -> bytes:
        return data


class Request:

    def __init__(
        self,
        method: Optional[str] = None,
        uri: Optional[str] = None,
        http_version: str = 'HTTP/1.1',
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None
    ):
        self.method = method
        self.uri = uri
        self.http_version = http_version
        self.headers = headers
        self.body = body

    @classmethod
    def from_bytes(cls, data: bytes):
        method, uri, http_version = cls._parse_method(data)
        headers: Dict[str, str] = cls._parse_headers(data)
        body: bytes = cls._parse_body(data)
        return cls(method, uri, http_version, headers, body)

    @staticmethod
    def _parse_headers(data: bytes) -> Dict[str, str]:
        bytes_headers: bytes = data.split(b'\r\n\r\n')[0]
        headers: Dict[str, str] = {}
        for line in bytes_headers.split(b'\r\n')[1:]:
            line_str: str = line.decode('utf-8')
            lines = line_str.split(': ')
            key: str = lines[0]
            val: str = ''.join(lines[1:])
            headers[key] = val
        return headers

    @staticmethod
    def _parse_body(data: bytes) -> bytes:
        request_components: List[bytes] = data.split(b'\r\n\r\n')
        if len(request_components) >= 2:
            return request_components[1]
        return b''

    @staticmethod
    def _parse_method(data: bytes):
        lines: List[bytes] = data.split(b'\r\n')
        request_line: bytes = lines[0]
        words: List[bytes] = request_line.split(b' ')
        method = words[0].decode()

        uri = None
        http_version = 'HTTP/1.1'
        if len(words) > 1:
            uri = words[1].decode()
        if len(words) > 2:
            http_version = words[2].decode()
        return method, uri, http_version


class HTTPServer(TCPServer):

    def handle_request(self, data: bytes) -> bytes:
        request: Request = Request.from_bytes(data)
        print(request.headers, request.body)

        if request.method not in HTTP_METHODS:
            return self.handle_not_implemented(request)
        handler: Callable = getattr(self, f'handle_{request.method}')
        return handler(request)

    def handle_not_implemented(self, request: Request) -> bytes:
        response_line: bytes = self._make_response_line(status_code=501)
        response_headers = self._make_response_headers()
        blank_line: bytes = b'\r\n'

        response_body: bytes = b'''
            <html><body><h1>501: Not Implemented</h1><body></html>
        '''
        return b''.join([
            response_line, response_headers, blank_line, response_body
        ])

    def handle_GET(self, request: Request) -> bytes:
        status_code: int = 200
        response_line: bytes = self._make_response_line(status_code)
        response_headers = self._make_response_headers()
        blank_line: bytes = b'\r\n'

        response_body: bytes = b'''
            <html><body><h1>Request received!</h1><body></html>
        '''
        return b''.join([
            response_line, response_headers, blank_line, response_body
        ])

    @staticmethod
    def _make_response_line(status_code: int) -> bytes:
        reason: str = STATUS_CODES[status_code]
        return f'HTTP/1.1 {status_code} {reason}\r\n'.encode()

    @staticmethod
    def _make_response_headers(
        extra_headers: Optional[Dict[str, str]] = None
    ) -> bytes:
        headers: Dict[str, str] = {
            'Server': 'MyServer',
            'Content-Type': 'text/html',
        }
        if extra_headers:
            headers.update(extra_headers)

        ret_headers: str = ''
        for k, v in headers.items():
            ret_headers += f'{k}: {v}\r\n'

        return ret_headers.encode()
