import unittest

from lib.input_output.http.messages import \
    HttpRequestMessage, HttpResponseMessage


class MessagesTestCase(unittest.TestCase):
    def test_http_request_message(self):
        request_str = ("GET / HTTP/1.1\r\nHost: localhost\r\n"
                       "connection: keepalive\r\n\r\ntest body")

        message = HttpRequestMessage.parse_request(request_str)

        self.assertEqual(str(message), request_str)

    def test_http_request_without_body(self):
        request_str = ("GET / HTTP/1.1\r\nHost: localhost\r\n"
                       "connection: keepalive\r\n\r\n")

        message = HttpRequestMessage.parse_request(request_str)

        self.assertEqual(str(message), request_str)

    def test_http_response_message(self):
        response_str = ("HTTP/1.1 200 OK\r\naccess-control-allow-origin: *\r\n"
                        "content-language: en\r\n\r\nresponse body")

        message = HttpResponseMessage.parse_response(response_str)

        self.assertEqual(str(message), response_str)

    def test_http_response_without_body(self):
        response_str = ("HTTP/1.1 200 OK\r\naccess-control-allow-origin: *\r\n"
                        "content-language: en\r\n\r\n")

        message = HttpResponseMessage.parse_response(response_str)

        self.assertEqual(str(message), response_str)


if __name__ == '__main__':
    unittest.main()
