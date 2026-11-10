pipeline {
    agent {
        label 'linux-arm64'
    }
    
    stages {
        stage('Identify Execution Environment') {
            steps {
                sh 'hostname'
                sh 'uname -m'
                sh 'pwd'
                sh 'id'
            }
        }
        
        stage('Prepare Python environment') {
            steps {
                sh 'python3 -m venv --clear .venv'
                sh '.venv/bin/python -m pip install -r requirements.txt'
                sh '.venv/bin/python -m pip check'
            }
        }

        stage('Test') {
            steps {
                sh '.venv/bin/python manage.py test health'
            }
        }

        stage('Build wheel') {
            steps {
                dir('dist') {
                    deleteDir()
                }
                sh '.venv/bin/python -m pip wheel --no-deps --wheel-dir dist .'
            }
        }

        stage('Verify installed wheel') {
            steps {
                sh '''
                    set -eu

                    repo_dir="$PWD"
                    set -- "$repo_dir"/dist/*.whl

                    if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
                        echo "Expected exactly one wheel in dist/" >&2
                        exit 1
                    fi

                    wheel_path="$1"

                    verify_dir="$(mktemp -d)"
                    trap 'rm -rf -- "$verify_dir"' 0

                    python3 -m venv "$verify_dir/.venv"
                    verify_python="$verify_dir/.venv/bin/python"

                    "$verify_python" -m pip install \
                        -r "$repo_dir/requirements.txt" "$wheel_path"
                    "$verify_python" -m pip check

                    cd "$verify_dir"
                    "$verify_python" -I -c \
                        'import config, health; print(config.__file__); print(health.__file__)'
                    "$verify_python" -I -m django test health.tests --settings=config.settings
                '''
            }
        }

        stage('Archive wheel') {
            steps {
                archiveArtifacts artifacts: 'dist/*.whl', fingerprint: true, onlyIfSuccessful: true
            }
        }

        stage('Upload wheel') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'nexus-pypi-publisher',
                    usernameVariable: 'TWINE_USERNAME',
                    passwordVariable: 'TWINE_PASSWORD'
                )]) {
                    sh '''
                        set -- dist/*.whl
                        if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
                            echo "Expected exactly one wheel in dist/" >&2
                            exit 1
                        fi

                        export TWINE_REPOSITORY_URL='http://nexus:8081/repository/pypi-releases/'
                        .venv/bin/python -m twine upload --non-interactive "$1"
                        '''
                }
            }
        }

        stage('Check wheel') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'nexus-pypi-viewer',
                    usernameVariable: 'NEXUS_USERNAME',
                    passwordVariable: 'NEXUS_PASSWORD'
                )]) {
                    sh '''
                    set +x
                    set -eu

                    set -- dist/*.whl
                    if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
                        echo "Expected exactly one wheel in dist/" >&2
                        exit 1
                    fi

                    wheel=$1
                    download_dir=$(mktemp -d)
                    trap 'rm -rf "$download_dir"' EXIT

                    .venv/bin/python - "$wheel" "$download_dir" <<'PY'
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from packaging.utils import parse_wheel_filename
name, version, _, _ = parse_wheel_filename(Path(sys.argv[1]).name)
username = quote(os.environ["NEXUS_USERNAME"], safe="")
password = quote(os.environ["NEXUS_PASSWORD"], safe="")
index_url = (
    f"http://{username}:{password}@nexus:8081"
    "/repository/pypi-releases/simple/"
)

subprocess.run(
    [sys.executable, "-m", "pip", "--disable-pip-version-check", "download",
     "--no-input", "--no-deps", "--only-binary=:all:", "--no-cache-dir",
     "--trusted-host", "nexus:8081", "--dest", sys.argv[2],
     f"{name}=={version}"],
    env={**os.environ, "PIP_INDEX_URL": index_url},
    check=True,
)
PY
                    downloaded="$download_dir/${wheel##*/}"
                    up_sum=$(sha256sum < "$wheel")
                    down_sum=$(sha256sum < "$downloaded")

                    if [ "$up_sum" != "$down_sum" ]; then
                        echo "Nexus wheel SHA-256 mismatch" >&2
                        sha256sum "$wheel" "$downloaded" >&2
                        exit 1
                    fi

                    echo "Nexus wheel SHA-256 verified: ${up_sum%% *}"
                '''
                }
            }
        }
    }
}