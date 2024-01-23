pipeline { 
    agent any
    environment{
        imageName="""etf_tool:${BUILD_NUMBER}"""
        containerName='ETFtool'
    }
    stages {
        stage('Build') {
            steps{
                sh 'docker system prune -af'
                sh 'docker build -t ${imageName} .'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker stop $containerName || true && docker rm -f $containerName || true'
                sh 'docker run -i -t -d -p 7070:7070 --name $containerName $imageName'
            }
        }
    }
}
