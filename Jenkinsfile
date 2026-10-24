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
    }
}