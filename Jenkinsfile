pipeline { 
    agent any 
    options {
        skipStagesAfterUnstable()
    }
    stages {
        stage('Build') { 
            steps { 
                pip 'install -r requirements.txt'
            }
        }
        stage('Deploy') {
            steps {
                flask '--app server run'
            }
        }
    }
}
