# Azure Delivery Platform

This project builds a reproducible delivery platform for a small Django service.
It combines Django development, Jenkins automation, and eventually Azure infrastructure
managed through Terraform.

This is a quick baseline/showcase project. Capabilities below distinguish demonstrated behavior from planned work.

## Current Implementation

- `/health/` endpoint returning HTTP `200` and `{"status": "ok"}`.
- An automated response-contract test using Django's `SimpleTestCase`.
- Setup verified from a fresh clone and isolated Python environment.
- A local Jenkins controller running through Docker Compose.
- Persistent Jenkins configuration stored in a named volume.
- A separate Jenkins agent connected over WebSocket.
- A successful pipeline demonstrating execution on the agent.
- Jenkins builds, tests, and archives a versioned Python wheel.
- Nexus stores the wheel, and Jenkins verifies the downloaded copy against the original SHA-256 digest.

## Technology

| Component | Current configuration |
|---|---|
| Local application runtime | Python 3.13.16 |
| Application framework | Django 6.1.2 |
| Development machine | Apple Silicon Mac |
| Jenkins controller image | `jenkins/jenkins:2.580.1-jdk21` |
| Container platform | `linux/arm64` |
| Agent node name | `build-agent-1` |
| Agent label | `linux-arm64` |
| Package repository | Nexus Repository, hosted PyPI repository `pypi-releases` |
| Wheel upload client | Twine 7.0.0 |

## Local Application Setup

### Prerequisites

- Git
- Python 3.13
- Docker Desktop with Docker Compose for the Jenkins lab

### Clone and Install

```bash
git clone https://github.com/TylerGolpe/azure-delivery-platform.git
cd azure-delivery-platform

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Verify

```bash
python -m pip check
python manage.py test health
```

Expected: no broken requirements and one passing test.

The health test does not require database setup.

### Run the Development Server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/health/.

Expected response:

```json
{"status": "ok"}
```

This endpoint checks that Django responds. It does not establish database readiness.

## Local Jenkins Lab

### Controller

The controller is available at http://127.0.0.1:8080/.

- Published access is restricted to the Mac's loopback address.
- Jenkins state persists in the `jenkins_home` named volume.
- Built-in node executors are manually configured to `0`.
- Controller configuration has survived a demonstrated container replacement.

### Agent

| Setting | Value |
|---|---|
| Node name | `build-agent-1` |
| Label | `linux-arm64` |
| Executors | `1` |
| Remote root directory | `/home/jenkins/agent` |
| Connection | Inbound WebSocket |
| Internal controller URL | `http://jenkins-controller:8080/` |

The agent image is pinned by digest in docker/jenkins-agent/Dockerfile.

### First-Time Initialization

When first connecting to the controller, you'll need to check the creation logs to find the initial administrator password. 

```bash
cp .env.example .env
JENKINS_AGENT_SECRET=bootstrap-placeholder docker compose up -d jenkins-controller
```

This will start *just* the controller. You can then obtain the initial admin password:

```bash
JENKINS_AGENT_SECRET=bootstrap-placeholder docker compose exec jenkins-controller cat /var/jenkins_home/secrets/initialAdminPassword
```

After this, proceed with the recommended plugins, and create the first admin account. 
After this, the default Built-in Node needs the executors set to 0. 
Then, the build-agent-1 node will need to be created, with the following settings:
 - Number of executors: 1
 - Remote root directory: /home/jenkins/agent
 - Labels: linux-arm64
 - Usage: Only build jobs with label expressions matching this node
 - Launch method: Launch agent by connecting it to the controller
 - Availability: Keep this agent online as much as possible

 After initialization and node registration, put the real agent secret in `.env` and run:

 ```bash
 docker compose up -d build-agent
 ```

### Agent Secret Configuration

After creating the agent, you'll be able to see some example boxes. In these boxes, you can find the agent secret needed to fill out the .env variable.

### Start and Stop

After completing the required local secret configuration:

```bash
docker compose up -d
docker compose ps
```

Stop the lab while retaining its containers and volumes:

```bash
docker compose stop
```

### Logs

```bash
docker compose logs --tail=40 jenkins-controller
docker compose logs --tail=40 build-agent
```

## Pipeline

### Agent Execution Check

The initial pipeline successfully demonstrated:

- Execution on `build-agent-1`.
- Linux ARM64 architecture reported as `aarch64`.
- A workspace under `/home/jenkins/agent/workspace/`.
- Commands running as the `jenkins` user.

Jenkins loads the root Jenkinsfile from main, and checks out the repository on the agent. 

The `agent-execution-check` job uses **Pipeline script from SCM** with **Git**.
Set the repository URL to `https://github.com/TylerGolpe/azure-delivery-platform.git`, the branch specifier to `*/main`, and the script path to `Jenkinsfile`.
The public repository can be checked out without a GitHub credential.

## Repository-Backed CI

Jenkins loads the root `Jenkinsfile` from the repository's `main` branch.
The pipeline checks out the source and runs on the separate agent selected
by the `linux-arm64` label.

The pipeline currently:

1. Reports the agent's execution environment.
2. Clears and recreates a workspace-local Python virtual environment.
3. Installs the versions recorded in `requirements.txt`.
4. Checks dependency compatibility with `pip check`.
5. Runs the Django health endpoint's response-contract test.
6. Clears `dist/` and builds the application wheel.
7. Installs the wheel in a fresh temporary virtual environment and runs the health test outside the checkout.
8. Archives and fingerprints the verified wheel on the Jenkins build.
9. Uploads that wheel to Nexus with Twine using the publisher credential.
10. Downloads the exact package version into a fresh directory with pip's cache disabled. Compares its SHA-256 digest with the workspace wheel and fails the build if they differ.

A deliberate incorrect health response caused the Test stage and pipeline
to fail. Reverting the change restored a successful build.

### Agent Runtime

The custom agent image is built from
`docker/jenkins-agent/Dockerfile`, extending a digest-pinned Jenkins
inbound-agent image with Python and virtual-environment support.

Build execution uses the non-root `jenkins` user.

Verified Python versions:

- Developer environment: Python 3.13.16.
- Jenkins agent: Python 3.13.5.

### Dependency Files

- `requirements.in` records the direct dependencies for the lab, including Django and Twine.
- `requirements.txt` pins the versions installed by the local setup and Jenkins.
- `pyproject.toml` declares the installable application's metadata and
  runtime requirements.

Runtime package versions are pinned. Build-tool versions and OS package
repositories are not fully locked.

## Application Packaging

The service can be built as a Python wheel using the setuptools
configuration in `pyproject.toml`.

Current package version is `0.1.1`.

```bash
python -m pip wheel --no-deps --wheel-dir dist .
```

Expected output:

```text
dist/azure_delivery_platform-0.1.1-py3-none-any.whl
```

The wheel contains the `config` and `health` Python packages, including
the health test and migrations package. Django is declared as a dependency;
its code is installed separately by pip.

Generated wheels and build directories are excluded from Git.

### Installed-Artifact Verification

The first wheel was installed into a fresh temporary virtual environment
alongside the pinned runtime requirements.

Verification ran outside the source checkout, using Python's isolated mode.
Both `config` and `health` resolved from the temporary environment's
`site-packages` directory.

Results:

- Package imports resolved from the installed wheel.
- `pip check` reported no broken requirements.
- One health contract test passed using the installed application.

The Jenkins `Verify installed wheel` stage now repeats this check on each build. It runs `health.tests` with `--settings=config.settings` and prints the import paths for `config` and `health` before archiving the wheel.

### Nexus Publication and Verification

Nexus is provisioned separately from the Jenkins Compose file. Create a hosted PyPI repository named `pypi-releases` and make Nexus reachable from the agent on a shared Docker network as `nexus:8081`.

| Operation | Agent-side URL | Jenkins credential ID |
| --- | --- | --- |
| Publish with Twine | `http://nexus:8081/repository/pypi-releases/` | `nexus-pypi-publisher` |
| Download with pip | `http://nexus:8081/repository/pypi-releases/simple/` | `nexus-pypi-viewer` |

Add both as **Username with password** credentials in Jenkins. Scope the publisher to publishing and the viewer to reading this repository. The lab currently allows redeploys so repeated test runs can reuse the same version.

A successful `Check wheel` stage prints `Nexus wheel SHA-256 verified:` followed by the digest. The manual Nexus download of `0.1.1` also matched the archived wheel from the publishing build.

To repeat that manual comparison, open the publishing build in Jenkins and open the `artifact/` page under its build URL. Download the wheel under `dist/` and compare it with the Nexus download using `shasum -a 256` on macOS or `sha256sum` on Linux. Compare the two digests from the same build and publication. A wheel built separately on the Mac can have the same filename and different bytes.

## Current Checkpoint

Completed:

- Local Django health endpoint and automated contract test.
- Setup verified from a fresh Git clone.
- Persistent Jenkins controller and separate connected agent.
- Repository-backed pipeline with dependency installation and testing.
- Demonstrated CI failure detection and restoration.
- Wheel built, installed, tested, and archived by Jenkins.
- Nexus publication and fresh download verified by matching SHA-256 digests.

Next:

- Build the application container image from the verified wheel retrieved from Nexus.

## Planned Work

- Build application container images from versioned wheels and publish them to Azure Container Registry.
- Deploy to Azure.
- Define Azure infrastructure with Terraform.
- Add readiness and deployed-release checks.
- Demonstrate controlled promotion, rollback, and recovery.

## Current Limitations

- The demonstrated Jenkins lab runs locally on one Mac.
- Jenkins initialization and node registration include manual UI configuration.
- The health endpoint does not check database connectivity.
- No Azure deployment or Terraform infrastructure has been demonstrated.
- Production readiness and high availability have not been established.
