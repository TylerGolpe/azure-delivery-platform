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

The agent image is pinned by digest in `compose.yaml`.

### First-Time Initialization

When first connecting to the controller, you'll need to check the creation logs to find the initial administrator password. 

```bash
cp .env.example .env
JENKINS_AGENT_SECRET=bootstrap-placeholder docker compose up -d jenkins-controller
```

This will start *just* the controller. You can then obtain the initial admin password:

```bash
docker compose exec jenkins-controller cat /var/jenkins_home/secrets/initialAdminPassword
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

 After intiialization and node regestration, put the real agent secret in .env, and run:

 ```bash
 docker compose up -d built-agent
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

The job's Pipeline, named "agent-execution-check", pulls the Pipeline script from SCM. The SCM is Git, the repository url is (this url .git), using no credentials since it's a public repo, and we specify that the brances to build is '*/main' instead of the default master.
The script path will default to Jenkinsfile.

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

- `requirements.in` records the application's chosen direct dependency.
- `requirements.txt` pins the resolved runtime dependency versions.
- `pyproject.toml` declares the installable application's metadata and
  runtime requirements.

Runtime package versions are pinned. Build-tool versions and OS package
repositories are not fully locked.

## Application Packaging

The service can be built as a Python wheel using the setuptools
configuration in `pyproject.toml`.

Current package version: `0.1.0`.

```bash
python -m pip wheel --no-deps --wheel-dir dist .
```

Expected output:

```text
dist/azure_delivery_platform-0.1.0-py3-none-any.whl
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

This demonstrates local wheel installation and test execution.
Wheel building and verification have not yet been added to Jenkins.

## Current Checkpoint

Completed:

- Local Django health endpoint and automated contract test.
- Setup verified from a fresh Git clone.
- Persistent Jenkins controller and separate connected agent.
- Repository-backed pipeline with dependency installation and testing.
- Demonstrated CI failure detection and restoration.
- Locally built wheel verified outside the source checkout.

Next:

- Build the wheel in Jenkins.
- Verify installation in a fresh environment outside the checkout.
- Retain the verified wheel as a Jenkins build artifact.
- Introduce Nexus for package storage.

## Planned Work

- Run application tests through Jenkins.
- Package versioned application artifacts.
- Introduce Nexus Repository.
- Build and publish application container images.
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