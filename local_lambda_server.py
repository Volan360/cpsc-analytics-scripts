#!/usr/bin/env python3
"""
Local Lambda Server for CPSC Analytics
=======================================

Simulates AWS Lambda invocations locally using Python's built-in HTTP server.
Listens on port 9001 (configurable) and routes AWS SDK Lambda invoke calls
to the appropriate Python handler functions.

Usage:
    python local_lambda_server.py [--port 9001] [--host localhost]

Then configure Spring Boot with:
    LAMBDA_ENDPOINT_URL=http://localhost:9001

The server handles POST requests to:
    /2015-03-31/functions/{functionName}/invocations

Routing:
    - Function names containing "report"               → report_handler.handler
    - Function names containing "generate" or "analytics" → analytics_handler.handler

Requirements:
    - Run from the cpsc-analytics-scripts/ directory, OR ensure venv/src is on PYTHONPATH
    - AWS credentials configured (for DynamoDB/S3 access, even locally)
"""

import argparse
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Path setup — ensure src/ is importable regardless of working directory
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(_SCRIPT_DIR, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ---------------------------------------------------------------------------
# Lazy-import handlers (deferred so import errors are reported clearly)
# ---------------------------------------------------------------------------
_analytics_handler = None
_report_handler = None


def _load_handlers():
    global _analytics_handler, _report_handler
    if _analytics_handler is None:
        from lambda_handlers.analytics_handler import lambda_handler as ah
        _analytics_handler = ah
    if _report_handler is None:
        from lambda_handlers.report_handler import lambda_handler as rh
        _report_handler = rh


# ---------------------------------------------------------------------------
# Mock Lambda context
# ---------------------------------------------------------------------------
class _MockContext:
    """Minimal stand-in for the Lambda context object."""
    function_name = "local-lambda"
    function_version = "$LATEST"
    invoked_function_arn = "arn:aws:lambda:us-east-1:000000000000:function:local-lambda"
    memory_limit_in_mb = 256
    aws_request_id = "00000000-0000-0000-0000-000000000000"
    log_group_name = "/aws/lambda/local-lambda"
    log_stream_name = "local"
    remaining_time_in_millis = 30000

    def get_remaining_time_in_millis(self):
        return self.remaining_time_in_millis


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------
class LambdaInvocationHandler(BaseHTTPRequestHandler):
    """
    Handles POST /2015-03-31/functions/{functionName}/invocations

    This is the exact path the AWS SDK uses when an endpointOverride is
    configured on the LambdaClient bean.
    """

    # Suppress default request logging (we do our own)
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Expected format: /2015-03-31/functions/{functionName}/invocations
        prefix = "/2015-03-31/functions/"
        suffix = "/invocations"

        if not (path.startswith(prefix) and path.endswith(suffix)):
            self._send_error(400, f"Unexpected path: {path}")
            return

        function_name = path[len(prefix):-len(suffix)]
        log.info("← Invoke request for function: %s", function_name)

        # Read request body (the Lambda event JSON)
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            event = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            self._send_error(400, f"Invalid JSON payload: {exc}")
            return

        # Route to the correct handler
        handler_fn = self._resolve_handler(function_name)
        if handler_fn is None:
            self._send_error(404, f"No handler registered for function: {function_name}")
            return

        # Invoke the handler
        context = _MockContext()
        context.function_name = function_name
        try:
            log.debug("  Event: %s", json.dumps(event, indent=2))
            result = handler_fn(event, context)
            log.info("  → %s status_code=%s", function_name, result.get("statusCode"))
            self._send_json(200, result)
        except Exception as exc:
            log.exception("Handler raised an exception for function %s", function_name)
            self._send_error(500, str(exc))

    def _resolve_handler(self, function_name: str):
        """Return the Python handler callable for the given Lambda function name."""
        try:
            _load_handlers()
        except ImportError as exc:
            log.error("Failed to load Lambda handlers: %s", exc)
            return None

        name_lower = function_name.lower()
        if "report" in name_lower:
            return _report_handler
        if "generate" in name_lower or "analytics" in name_lower:
            return _analytics_handler

        log.warning("No routing match for function name: %s", function_name)
        return None

    def _send_json(self, status_code: int, body):
        """Send a JSON HTTP response."""
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status_code: int, message: str):
        """Send a plain-text error response and log it."""
        log.error("HTTP %d: %s", status_code, message)
        payload = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Local Lambda invocation server for CPSC Analytics"
    )
    parser.add_argument("--host", default="localhost",
                        help="Host to listen on (default: localhost)")
    parser.add_argument("--port", type=int, default=9001,
                        help="Port to listen on (default: 9001)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level (default: INFO)")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Pre-load handlers so import errors surface immediately
    log.info("Loading Lambda handlers...")
    try:
        _load_handlers()
        log.info("  ✓ analytics_handler loaded")
        log.info("  ✓ report_handler loaded")
    except ImportError as exc:
        log.error("Failed to import handlers — check your PYTHONPATH and venv: %s", exc)
        sys.exit(1)

    server = HTTPServer((args.host, args.port), LambdaInvocationHandler)
    log.info("Local Lambda server listening on http://%s:%d", args.host, args.port)
    log.info("Configure Spring Boot with: LAMBDA_ENDPOINT_URL=http://%s:%d", args.host, args.port)
    log.info("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down local Lambda server.")
        server.server_close()


log = logging.getLogger(__name__)

if __name__ == "__main__":
    main()
