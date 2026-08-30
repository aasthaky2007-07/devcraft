from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from parser import parse_record


class RequestHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        response = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.end_headers()

        self.wfile.write(response)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.end_headers()

    def do_POST(self):

        if self.path != "/parse":
            self.send_json(
                {"error": "Endpoint not found"},
                404
            )
            return

        try:
            length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(length)

            data = json.loads(
                body.decode("utf-8")
            )

            message = data.get("message", "")
            domain = data.get(
                "domain",
                "Electrician"
            )

            if not message.strip():
                self.send_json(
                    {"error": "Message is empty"},
                    400
                )
                return

            record = {
                "id": "app-order",
                "domain": domain.lower(),
                "received_at": "2026-09-01T08:00:00+05:30",
                "message": message,
            }

            result = parse_record(record)

            self.send_json(result)

        except Exception as error:
            self.send_json(
                {
                    "error": str(error)
                },
                500
            )


server = HTTPServer(
    ("localhost", 8000),
    RequestHandler
)

print("DevCraft parser API running...")
print("http://localhost:8000")

server.serve_forever()