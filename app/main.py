import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template

app = Flask(__name__)

BUILD_INFO = {
    "build_number": os.getenv("BUILD_NUMBER", "local"),
    "git_commit": os.getenv("GIT_COMMIT", "unknown"),
    "git_branch": os.getenv("GIT_BRANCH", "unknown"),
    "build_time": os.getenv("BUILD_TIME", "unknown"),
    "app_version": os.getenv("APP_VERSION", "0.0.0"),
}
STARTED_AT = datetime.now(timezone.utc)


def runtime_info():
    return {
        "environment": os.getenv("APP_ENV", "local"),
        "cluster": os.getenv("CLUSTER_NAME", "none"),
        "namespace": os.getenv("POD_NAMESPACE", "none"),
        "pod": os.getenv("POD_NAME", os.uname().nodename),
        "started_at": STARTED_AT.isoformat(timespec="seconds"),
        "uptime_seconds": int((datetime.now(timezone.utc) - STARTED_AT).total_seconds()),
    }


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.get("/ready")
def ready():
    # DELIBERATE FAULT (rollback demonstration): this build reports itself
    # permanently not-ready. Kubernetes will therefore never send it traffic,
    # the rollout cannot complete, and the pipeline must detect and revert it.
    return jsonify(status="not-ready", reason="simulated defect"), 503


@app.get("/api/build-info")
def build_info():
    return jsonify(build=BUILD_INFO, runtime=runtime_info())


@app.get("/")
def index():
    return render_template("index.html")
