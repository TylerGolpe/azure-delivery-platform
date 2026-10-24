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