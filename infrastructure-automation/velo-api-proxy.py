#!/usr/bin/env python3
"""
Velociraptor REST-to-gRPC API Proxy
Exposes Velociraptor VQL queries over HTTPS REST for Shuffle SOAR integration.
Uses mTLS gRPC to communicate with Velociraptor server.
"""
import json
import ipaddress
import os
import sys
import grpc
import yaml
from flask import Flask, request, jsonify
from functools import wraps
from pyvelociraptor import api_pb2, api_pb2_grpc

app = Flask(__name__)

# Configuration
API_CONFIG_PATH = os.environ.get("VELO_CONFIG_PATH", "/opt/velo-api-proxy/shuffle-api-client.yaml")
API_KEY = os.environ.get("VELO_API_KEY", "CHANGE_ME")  # Set via VELO_API_KEY env var
LISTEN_PORT = 8890

# Load Velociraptor API client config
with open(API_CONFIG_PATH) as f:
    config = yaml.safe_load(f)


def get_grpc_channel():
    """Create authenticated gRPC channel to Velociraptor"""
    creds = grpc.ssl_channel_credentials(
        root_certificates=config["ca_certificate"].encode("utf-8"),
        private_key=config["client_private_key"].encode("utf-8"),
        certificate_chain=config["client_cert"].encode("utf-8"),
    )
    options = (("grpc.ssl_target_name_override", "VelociraptorServer",),)
    target = config["api_connection_string"]
    return grpc.secure_channel(target, creds, options)


def run_vql(vql_query, env=None):
    """Execute VQL query and return results"""
    channel = get_grpc_channel()
    stub = api_pb2_grpc.APIStub(channel)

    vql_env = []
    if env:
        for k, v in env.items():
            vql_env.append(api_pb2.VQLEnv(key=k, value=v))

    request_obj = api_pb2.VQLCollectorArgs(
        max_wait=10,
        max_row=1000,
        Query=[api_pb2.VQLRequest(VQL=vql_query)],
        env=vql_env,
    )

    results = []
    for response in stub.Query(request_obj):
        if response.Response:
            try:
                rows = json.loads(response.Response)
                results.extend(rows)
            except json.JSONDecodeError:
                pass

    channel.close()
    return results


def require_api_key(f):
    """Simple API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if auth != "Bearer " + API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route("/api/vql", methods=["POST"])
@require_api_key
def vql_query():
    """Execute arbitrary VQL query"""
    data = request.get_json()
    if not data or "vql" not in data:
        return jsonify({"error": "Missing vql field"}), 400
    try:
        results = run_vql(data["vql"], data.get("env"))
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/clients", methods=["GET"])
@require_api_key
def list_clients():
    """List all connected clients"""
    try:
        results = run_vql(
            "SELECT client_id, os_info.hostname AS hostname, "
            "os_info.system AS os, last_seen_at FROM clients()"
        )
        return jsonify({"success": True, "clients": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/clients/find", methods=["POST"])
@require_api_key
def find_client():
    """Find client by hostname"""
    data = request.get_json()
    hostname = data.get("hostname", "")
    if not hostname:
        return jsonify({"error": "Missing hostname"}), 400
    try:
        results = run_vql(
            "SELECT client_id, os_info.hostname AS hostname "
            "FROM clients() WHERE os_info.hostname =~ '" + hostname + "'"
        )
        return jsonify({"success": True, "clients": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/collect", methods=["POST"])
@require_api_key
def collect_artifact():
    """Collect artifact from a client"""
    data = request.get_json()
    client_id = data.get("client_id")
    artifacts = data.get("artifacts", [])
    if not client_id or not artifacts:
        return jsonify({"error": "Missing client_id or artifacts"}), 400

    artifacts_str = ", ".join('"' + a + '"' for a in artifacts)
    vql = (
        "SELECT collect_client(client_id='" + client_id
        + "', artifacts=[" + artifacts_str + "]) FROM scope()"
    )
    try:
        results = run_vql(vql)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Generate self-signed cert for HTTPS
    cert_path = os.environ.get("VELO_CERT_PATH", "/opt/velo-api-proxy/proxy-cert.pem")
    key_path = os.environ.get("VELO_KEY_PATH", "/opt/velo-api-proxy/proxy-key.pem")

    if not os.path.exists(cert_path):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "velo-api-proxy"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.IPv4Address("10.0.1.20")),
                x509.DNSName("velociraptor-server"),
            ]), critical=False)
            .sign(key, hashes.SHA256())
        )

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            ))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        os.chmod(key_path, 0o600)

    app.run(host="0.0.0.0", port=LISTEN_PORT, ssl_context=(cert_path, key_path))
