pipeline { 
    agent { dockerfile true } 
    stages {
        stage('Deploy') {
            environment{
                imageName=ETFtool:${BUILD_NUMBER}
                containerName=ETFtool
            }
            steps {
                

                sh 'docker system prune -af'
                sh 'docker build -t ${imageName}'
                sh 'docker stop $containerName || true && docker rm -f $containerName || true'
                sh 'docker run --name $containerName $imageName
                
                sh 'echo done'
            }
        }
    }
}
