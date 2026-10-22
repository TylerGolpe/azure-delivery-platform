My account hosts an astonishing lack of anything important/production quality.
This won't change, but I do want to at least fluff it up.

The goal of this project is to build a basic delivery platform for a Django service.
Current implementation: /health/ and it's automated reponse test
Current runtime: Python 3.13.16 & Django 6.1.2 (Would've been 3.15 if 6.1.3 was out)
Local setup: Create/activate a virtual env, install requirements.txt, run the test and development server.

To do:
- Add Terraform
- Add Azure deployment

The current deployment so far can be verified by cloning the git repo, creating a python3.13 venv, and
then installing the reqs using pip before checking with python manage.py test health





A Jenkins container has been setup via Docker.
Image: jenkins/jenkins:2.580.1-jdk21, platform linux/arm64
Jenkins state persists in the jenkins_home named volume.
Built-in executors are currently manually configured to 0.