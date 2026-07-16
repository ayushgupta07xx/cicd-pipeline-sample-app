import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Exposes /metrics in Prometheus exposition format. Request count and latency
# histograms are recorded automatically per endpoint.
metrics = PrometheusMetrics(app, group_by="endpoint")

BUILD_INFO = {
    "build_number": os.getenv("BUILD_NUMBER", "local"),
    "git_commit": os.getenv("GIT_COMMIT", "unknown"),
    "git_branch": os.getenv("GIT_BRANCH", "unknown"),
    "build_time": os.getenv("BUILD_TIME", "unknown"),
    "app_version": os.getenv("APP_VERSION", "0.0.0"),
}
STARTED_AT = datetime.now(timezone.utc)

# Build identity as a labelled gauge: a metric can therefore be attributed to
# the exact commit that produced the running artifact.
# Labels match orders-api exactly so a single dashboard query covers both
# services — consistent instrumentation is what makes cross-service views work.
metrics.info(
    "app_build_info",
    "Build metadata; labels carry the artifact identity",
    build_number=BUILD_INFO["build_number"],
    commit=BUILD_INFO["git_commit"][:7],
    branch=BUILD_INFO["git_branch"],
    version=BUILD_INFO["app_version"],
    environment=os.getenv("APP_ENV", "local"),
    cluster=os.getenv("CLUSTER_NAME", "none"),
)


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
    # Conditional on APP_ENV, which the Deployment injects at deploy time and
    # which is absent when the suite runs in CI. The tests therefore pass and
    # the image builds — exactly as a config-dependent bug behaves in practice.
    #
    # In-cluster the pod reports permanently not-ready, so Kubernetes never
    # routes traffic to it, the rollout cannot complete, and the pipeline must
    # detect the stall and revert on its own.
    if os.getenv("APP_ENV"):
        return jsonify(status="not-ready", reason="simulated environment-specific defect"), 503
    return jsonify(status="ready"), 200


@app.get("/api/build-info")
def build_info():
    return jsonify(build=BUILD_INFO, runtime=runtime_info())


@app.get("/")
def index():
    return render_template("index.html")
