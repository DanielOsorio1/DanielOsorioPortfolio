#!/usr/bin/env python3
from flask import Flask, jsonify, redirect
import json
import threading

app = Flask(__name__)
lock = threading.Lock()
count_file = "/data/tap_count.json"


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
