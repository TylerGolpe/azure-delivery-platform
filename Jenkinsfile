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
    }
}