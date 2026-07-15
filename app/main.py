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
    # DELIBERATE FAULT (rollback demonstration).
    #
    # This simulates the class of defect unit tests cannot catch: one that only
    # manifests once the service is running in a real environment. The fault is
    # conditional on APP_ENV, which is injected by the Deployment at deploy time
    # and is absent when the suite runs in CI — so the tests pass and the image
    # builds, exactly as a config-dependent bug would behave in practice.
    #
    # In-cluster the pod reports permanently not-ready, so Kubernetes never
    # routes traffic to it, the rollout cannot complete, and the pipeline must
    # detect the stall and revert to the previous revision on its own.
    if os.getenv("APP_ENV"):
        return jsonify(status="not-ready", reason="simulated environment-specific defect"), 503
    return jsonify(status="ready"), 200


@app.get("/api/build-info")
def build_info():
    return jsonify(build=BUILD_INFO, runtime=runtime_info())


@app.get("/")
def index():
    return render_template("index.html")
