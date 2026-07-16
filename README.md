<div align="center">

<img src="docs/images/logo-mark.svg" width="76" alt="CI/CD Pipeline logo" />

# CI/CD Pipeline — Sample App

### A Python service whose UI is a **delivery receipt** — build number, commit, cluster and pod, polled live. When the pipeline deploys, you watch it change. When it rolls back, you watch that too.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](#tech-stack)
[![tests](https://img.shields.io/badge/tests-5_passing-success)](#tests)
[![Jenkinsfile](https://img.shields.io/badge/Jenkinsfile-3_lines-E8A33D)](#onboarding-cost)
[![container](https://img.shields.io/badge/runs_as-UID_10001-success)](#security)
[![Trivy](https://img.shields.io/badge/Trivy-clean-success)](#security)

[![Python](https://img.shields.io/badge/Python_3.12-3776AB?logo=python&logoColor=white)](#tech-stack)
[![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)](#tech-stack)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?logo=gunicorn&logoColor=white)](#tech-stack)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](#tech-stack)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)](#tech-stack)
[![Jenkins](https://img.shields.io/badge/Jenkins-D24939?logo=jenkins&logoColor=white)](https://github.com/ayushgupta07xx/cicd-pipeline-shared-library)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)](#observability)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)](#tests)

<br/>

[![Watch the walkthrough](https://img.shields.io/badge/▶_Watch_the_9_min_walkthrough-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/8HLydMg_BCg)

📘 **[Read the case study](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/)** · ⚙️ **[Shared Library](https://github.com/ayushgupta07xx/cicd-pipeline-shared-library)** · 🟩 **[Orders API](https://github.com/ayushgupta07xx/cicd-pipeline-orders-api)** · 🏗 **[Platform](https://github.com/ayushgupta07xx/cicd-pipeline-platform)**

</div>

---

## The case study

A walkthrough of the design, the evidence behind every claim, and a constraints
section naming what this setup compromises and what production would do instead.

[![Case study — CI/CD Pipeline](docs/images/showcase-overview.png)](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/)

<div align="center">

**[→ Read the case study](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/)** ·
[Architecture](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/#architecture) ·
[Multi-repo](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/#multirepo) ·
[Security](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/#security) ·
[Failure handling](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/#failure) ·
[Constraints](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/#constraints)

</div>


Deployed by the **[shared delivery pipeline](https://github.com/ayushgupta07xx/cicd-pipeline-shared-library)**, and the host of the **[case study site](https://ayushgupta07xx.github.io/cicd-pipeline-sample-app/)**.

Most demo apps return a JSON blob and prove nothing. This one exists to make the pipeline's behaviour **visible**: its page reads from its own `/api/build-info`, which reads the environment variables the pipeline injected. Redeploy, and the build number rolls over on screen. Roll back, and it rolls back on screen. The event stream logs every poll with real measured latency — so a container swap shows up as a slow request and a couple of failures, because that's exactly what it is.

## Onboarding cost

Two files. That's the whole integration with the pipeline:

```groovy
// Jenkinsfile — identical in every repository
@Library('finacplus-cicd@main') _

deliveryPipeline()
```

Plus `deploy-config.yaml` declaring what this service is and which clusters it targets. **No pipeline logic lives here.**

## The receipt

The page proves the build/deploy metadata split, which is the heart of "build once, promote unchanged":

| Baked at **image build** — describes the artifact | Injected at **deploy** — describes where it landed |
|---|---|
| `BUILD_NUMBER` · `GIT_COMMIT` · `GIT_BRANCH` | `APP_ENV` · `CLUSTER_NAME` |
| `APP_VERSION` · `BUILD_TIME` | `POD_NAME` · `POD_NAMESPACE` *(downward API)* |

The same immutable image runs in staging and production — only the right-hand column differs. That's why one badge reads amber and the other reads red, and why "it passed in staging" is a statement about the exact bytes now in production.

## Endpoints

| Path | Purpose |
|---|---|
| `/` | Delivery receipt UI — live-polled build and runtime identity |
| `/health` | **Liveness** — is the process alive |
| `/ready` | **Readiness** — should it receive traffic |
| `/api/build-info` | Build and runtime identity as JSON |
| `/metrics` | Prometheus exposition, including `app_build_info` |

Separate liveness and readiness endpoints are deliberate. Pointing both at one path is the most common Kubernetes probe mistake: a briefly overloaded pod gets **killed** instead of taken out of rotation, turning a blip into an outage. It also makes the rollback demonstration possible — the injected fault leaves the pod alive but permanently unready, so the rollout stalls rather than crash-loops.

## Observability

```
app_build_info{service="sample-app", build_number="20", commit="bd5fd0b",
               branch="main", version="1.0.0",
               environment="staging", cluster="kind-staging"} 1
```

Three annotations on the pod template and Prometheus scrapes it from the moment it deploys — no monitoring config change, ever:

```yaml
prometheus.io/scrape: "true"
prometheus.io/port:   "8080"
prometheus.io/path:   "/metrics"
```

That gauge is what makes a latency regression attributable to a **commit** rather than a point in time.

## Security

```bash
$ docker run --rm sample-app:local id
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

Non-root UID 10001 · read-only root filesystem · all capabilities dropped · `seccompProfile: RuntimeDefault` · `automountServiceAccountToken: false` — the app never calls the Kubernetes API, so it carries no credential to steal. Trivy scans every image before it can be pushed.

## Run it locally

```bash
docker build -t sample-app:local .
docker run --rm -p 8099:8080 -e APP_ENV=local sample-app:local
# → http://localhost:8099
```

## Tests

```bash
docker run --rm -v "$(pwd)":/w -w /w python:3.12-slim \
  sh -c 'pip install -q -r requirements.txt pytest && python -m pytest -q'
```

Five tests: `/health`, `/ready`, the `/api/build-info` contract shape, the receipt rendering, and `/metrics` exposing `app_build_info`. They run in the **same image the pipeline uses**, which removes the "works on my machine" gap entirely.

## Tech stack

| Layer | Tools |
|---|---|
| Service | Python 3.12 · Flask 3 · Gunicorn (2 workers × 4 threads) |
| Metrics | `prometheus-flask-exporter` — request counters, latency histograms, build-identity gauge |
| UI | Single-file HTML/CSS/JS — no framework, no build step, polls `/api/build-info` every 5s |
| Container | `python:3.12-slim` pinned · non-root · read-only rootfs · OCI labels |
| Kubernetes | `${VAR}`-templated manifests · `maxUnavailable: 0` · separate probes · resource limits |
| Testing | pytest |
| Docs site | Static HTML on GitHub Pages — the case study |

## Repo layout

```
app/
  main.py                Flask app — endpoints + build/runtime identity
  templates/index.html   the delivery receipt UI
k8s/
  deployment.yaml        Deployment · Service · ServiceAccount (templated)
  rbac-deployer.yaml     least-privilege Role for the pipeline
  namespace.yaml
tests/test_app.py        5 tests
docs/                    the case study site (GitHub Pages)
Jenkinsfile              3 lines
deploy-config.yaml       the entire integration with the pipeline
```

## Honest limitations

- **The app is deliberately trivial.** It exists to make the pipeline observable, not to be interesting. A real service would earn a multi-stage build and a distroless runtime.
- **The receipt UI is not a product.** It's a verification surface — the fastest way to see a deploy actually landed.

## License

Code under **Apache 2.0** — see [`LICENSE`](LICENSE).

---

<div align="center">

Built by **Ayush Gupta** · [GitHub](https://github.com/ayushgupta07xx) · [LinkedIn](https://www.linkedin.com/in/ayush-gupta-544a803a2)

</div>
