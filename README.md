# cicd-pipeline-sample-app

A containerised Python/Flask service (auto-deployed on commit) deployed by the
[shared delivery pipeline](https://github.com/ayushgupta07xx/cicd-pipeline-shared-library).

Onboarding this service required exactly two files: a three-line `Jenkinsfile`
and `deploy-config.yaml`. No pipeline logic lives here.

## What it demonstrates

The service exists to make the pipeline's behaviour observable. Its UI is a
**delivery receipt**: build number, commit SHA, branch, environment, cluster and
pod name, polled live from `/api/build-info`.

That distinction is the point. `BUILD_NUMBER`, `GIT_COMMIT` and `APP_VERSION`
are baked at **image build** — they describe the artifact. `APP_ENV` and
`CLUSTER_NAME` are injected at **deploy** — they describe where it landed. The
same immutable image runs in staging and production; only the runtime differs.

During a rollout the page shows the transition live, which is how a deploy — or
a rollback — is verified rather than assumed.

## Endpoints

| Path | Purpose |
|---|---|
| `/` | Delivery receipt UI |
| `/health` | Liveness probe — is the process alive |
| `/ready` | Readiness probe — should it receive traffic |
| `/api/build-info` | Build and runtime identity as JSON |
| `/metrics` | Prometheus exposition, including `app_build_info` |

Separate liveness and readiness endpoints are deliberate: pointing both at one
path is the most common Kubernetes probe mistake, and it means a struggling pod
gets killed instead of being taken out of rotation.

## Local run

```bash
docker build -t sample-app:local .
docker run --rm -p 8099:8080 -e APP_ENV=local sample-app:local
```

## Tests

```bash
docker run --rm -v "$(pwd)":/w -w /w python:3.12-slim \
  sh -c 'pip install -q -r requirements.txt pytest && python -m pytest -q'
```

## Security

Runs as UID 10001, read-only root filesystem, all capabilities dropped, no
ServiceAccount token mounted. Verify:

```bash
docker run --rm sample-app:local id
```

