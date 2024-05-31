from py_zipkin.transport import BaseTransportHandler
import requests


class ZipkinTransportHandler(BaseTransportHandler):
    def get_max_payload_bytes(self):
        return None

    def send(self, encoded_span):
        body = encoded_span
        print(body)
        requests.post(
            "http://localhost:9411/api/v2/spans",
            data=body,
            headers={'Content-Type': 'application/json'},
        )


zipkin_transport_handler = ZipkinTransportHandler()
