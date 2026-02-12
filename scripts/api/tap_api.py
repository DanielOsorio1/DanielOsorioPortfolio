#!/usr/bin/env python3
from flask import Flask, jsonify, redirect, request
import hashlib
import hmac
import json
import os
import subprocess
import threading

app = Flask(__name__)
lock = threading.Lock()
deploy_lock = threading.Lock()
count_file = "/data/tap_count.json"
deploy_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
deploy_cmd = ["/srv/sites/_bin/pull-from-github.sh", "osoriodaniel.net", "main"]
deploy_timeout_seconds = 120


# Initialize count file if it doesn't exist
try:
    with open(count_file, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"count": 0}
    with open(count_file, "w") as f:
        json.dump(data, f)


@app.route("/tap", methods=["GET"])
def tap():
    with lock:
        data["count"] += 1
        with open(count_file, "w") as f:
            json.dump(data, f)
    return redirect("/", code=302)


@app.route("/count", methods=["GET"])
def get_count():
    with lock:
        return jsonify(data)


def _valid_github_signature(raw_body: bytes, signature_header: str) -> bool:
    if not deploy_secret:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        deploy_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    if not deploy_secret:
        return jsonify({"error": "webhook secret is not configured"}), 503

    raw_body = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not _valid_github_signature(raw_body, signature):
        return jsonify({"error": "invalid signature"}), 403

    event = request.headers.get("X-GitHub-Event", "")
    if event == "ping":
        return jsonify({"ok": True, "event": "ping"}), 200
    if event != "push":
        return jsonify({"ok": True, "ignored_event": event}), 202

    payload = request.get_json(silent=True) or {}
    if payload.get("ref") != "refs/heads/main":
        return jsonify({"ok": True, "ignored_ref": payload.get("ref")}), 202

    with deploy_lock:
        try:
            result = subprocess.run(
                deploy_cmd,
                capture_output=True,
                text=True,
                timeout=deploy_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"error": "deploy command timed out"}), 504

    if result.returncode != 0:
        return (
            jsonify(
                {
                    "error": "deploy failed",
                    "stdout_tail": result.stdout[-2000:],
                    "stderr_tail": result.stderr[-2000:],
                }
            ),
            500,
        )

    return jsonify({"ok": True, "stdout_tail": result.stdout[-2000:]}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
