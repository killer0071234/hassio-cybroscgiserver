"""Status page for the CybroScgiServer, served through Home Assistant ingress.

Reads the status tags of the scgi server (sys.* and cNAD.sys.*) over its HTTP
interface and shows them on a small web page.
"""
import argparse
import json
import logging
import os
import re
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs
from xml.etree.ElementTree import fromstring

# requests from ingress always come from the supervisor
INGRESS_CLIENTS = {"172.30.32.2", "127.0.0.1", "::1"}
SCGI_TIMEOUT_S = 5

SYS_TAGS = [
    "scgi_status",
    "server_version",
    "server_uptime",
    "scgi_request_count",
    "push_port_status",
    "nad_list",
    "push_list",
]
PLC_TAGS = [
    "plc_status",
    "ip_port",
    "response_time",
    "com_error_count",
    "timestamp",
]

ORIGINS = {
    "static": "static",
    "push": "push",
    "auto": "autodetect",
    "proxy": "proxy",
}
# row of sys.push_list: "push received" (empty for static), nad, type, ...
# the columns are padded to a fixed width but longer values shift them,
# so match the values instead of the column positions
PUSH_LIST_ROW = re.compile(
    r"^\s*(?:\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})?\s*(\d+)\s+("
    + "|".join(ORIGINS)
    + r")\b"
)

INDEX_HTML = (Path(__file__).parent / "index.html").read_bytes()

log = logging.getLogger("status_gui")


def read_tags(scgi_url: str, tags: List[str]) -> Dict[str, object]:
    """Reads tags from the scgi server, returns a map of tag name to value.

    The value is a list for tags that return a list (e.g. sys.nad_list).
    """
    url = f"{scgi_url}/?{'&'.join(tags)}"
    with urllib.request.urlopen(url, timeout=SCGI_TIMEOUT_S) as response:
        root = fromstring(response.read())

    values: Dict[str, object] = {}
    for var in root.findall("var"):
        value = var.find("value")
        items = value.findall("item") if value is not None else []
        if items:
            values[var.findtext("name")] = [item.text or "" for item in items]
        else:
            values[var.findtext("name")] = var.findtext("value")
    return values


def read_variables(scgi_url: str, nad: int) -> List[Dict[str, str]]:
    """Reads the variable list of a controller (from its alc file)."""
    url = f"{scgi_url}/?c{nad}.sys.variables"
    with urllib.request.urlopen(url, timeout=SCGI_TIMEOUT_S) as response:
        root = fromstring(response.read())

    variables = []
    for var in root.findall("var"):
        # error responses (e.g. no alc file) have no type
        if var.find("type") is None:
            continue
        # the controller part of the name may be an alias, so drop it
        name = (var.findtext("name") or "").partition(".")[2]
        variables.append({
            "name": name,
            "type": var.findtext("type") or "",
            "description": var.findtext("description") or "",
        })
    return sorted(variables, key=lambda v: v["name"])


def parse_origins(push_list: object) -> Dict[int, str]:
    """Gets how each controller was added from the sys.push_list table."""
    origins: Dict[int, str] = {}
    if not isinstance(push_list, str):
        return origins
    for line in push_list.splitlines():
        match = PUSH_LIST_ROW.match(line)
        if match:
            origins[int(match[1])] = ORIGINS[match[2]]
    return origins


def get_status(scgi_url: str, app_version: Optional[str]) -> dict:
    status = {
        "app_version": app_version,
        "server_version": None,
        "state": "unreachable",
        "error": None,
        "uptime": None,
        "request_count": None,
        "push_port_status": None,
        "controllers": [],
    }

    try:
        sys_values = read_tags(scgi_url, [f"sys.{tag}" for tag in SYS_TAGS])
    except Exception as e:
        status["error"] = str(e)
        return status

    status["state"] = sys_values.get("sys.scgi_status") or "unknown"
    status["server_version"] = sys_values.get("sys.server_version")
    status["uptime"] = sys_values.get("sys.server_uptime")
    status["request_count"] = sys_values.get("sys.scgi_request_count")
    status["push_port_status"] = sys_values.get("sys.push_port_status")

    nad_list = sys_values.get("sys.nad_list") or []
    if isinstance(nad_list, str):
        # a single nad (or an empty list) is not returned as list
        nad_list = [nad_list] if nad_list.isdigit() else []
    nads = sorted({int(nad) for nad in nad_list if nad.isdigit()})
    if not nads:
        return status

    try:
        plc_values = read_tags(
            scgi_url,
            [f"c{nad}.sys.{tag}" for nad in nads for tag in PLC_TAGS]
        )
    except Exception as e:
        status["error"] = f"Could not read controller status: {e}"
        plc_values = {}

    origins = parse_origins(sys_values.get("sys.push_list"))
    for nad in nads:
        controller = {"nad": nad, "origin": origins.get(nad)}
        for tag in PLC_TAGS:
            controller[tag] = plc_values.get(f"c{nad}.sys.{tag}")
        status["controllers"].append(controller)

    return status


class Handler(BaseHTTPRequestHandler):
    scgi_url: str = ""
    app_version: Optional[str] = None

    def do_GET(self):
        if self.client_address[0] not in INGRESS_CLIENTS:
            self.send_error(403)
            return

        path, _, query = self.path.partition("?")
        if path in ("", "/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", INDEX_HTML)
        elif path == "/api/status":
            body = json.dumps(get_status(self.scgi_url, self.app_version))
            self._send(200, "application/json", body.encode())
        elif path == "/api/variables":
            nad = parse_qs(query).get("nad", [""])[0]
            if not nad.isdigit():
                self.send_error(400, "Invalid nad")
                return
            try:
                variables = read_variables(self.scgi_url, int(nad))
            except Exception as e:
                self.send_error(502, f"Could not read variables: {e}")
                return
            self._send(200, "application/json", json.dumps(variables).encode())
        else:
            self.send_error(404)

    def _send(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        log.debug("%s - %s", self.address_string(), format % args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--scgi-port", type=int, default=4000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    Handler.scgi_url = f"http://127.0.0.1:{args.scgi_port}"
    Handler.app_version = os.environ.get("APP_VERSION") or None

    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    log.info("Status page listening on %s:%d", args.bind, args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
