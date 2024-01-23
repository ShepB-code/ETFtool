pipeline { 
    agent { dockerfile true } 
    stages {
        stage('Deploy') {
            steps {
                sh 'python ./server.py'
            }
        }
    }
}
