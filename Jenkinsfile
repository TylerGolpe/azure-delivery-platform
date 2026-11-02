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
    }
}