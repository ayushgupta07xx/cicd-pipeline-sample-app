from app.main import app


def test_health_ok():
    c = app.test_client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_ready_ok():
    c = app.test_client()
    assert c.get("/ready").status_code == 200


def test_build_info_shape():
    c = app.test_client()
    d = c.get("/api/build-info").get_json()
    assert "build" in d and "runtime" in d
    for k in ("build_number", "git_commit", "git_branch", "app_version"):
        assert k in d["build"]
    for k in ("environment", "cluster", "namespace", "pod"):
        assert k in d["runtime"]


def test_index_renders():
    c = app.test_client()
    r = c.get("/")
    assert r.status_code == 200
    assert b"DELIVERY RECEIPT" in r.data


def test_metrics_endpoint_exposes_prometheus_format():
    c = app.test_client()
    r = c.get("/metrics")
    assert r.status_code == 200
    body = r.data.decode()
    assert "app_build_info" in body
    assert "flask_http_request" in body or "python_info" in body
