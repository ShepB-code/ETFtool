pipeline { 
    agent any
    stages {
        environment{
                imageName="""ETFtool:${BUILD_NUMBER}"""
                containerName='ETFtool'
        }
        stage('Build') {
            steps{
                sh 'docker system prune -af'
                sh 'docker build -t ${imageName}'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker stop $containerName || true && docker rm -f $containerName || true'
                sh 'docker run --name $containerName $imageName'
            }
        }
    }
}
