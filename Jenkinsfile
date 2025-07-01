pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "flaskci"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/zacst/learn-devops.git'
            }
        }

        // stage('Build and Start Services') {
        //     steps {
        //         script {
        //             sh 'docker-compose down -v' // clean previous runs
        //             sh 'docker-compose build'
        //             sh 'docker-compose up -d'
        //         }
        //     }
        // }

        // stage('Wait for App to Start') {
        //     steps {
        //         script {
        //             // Simple retry loop to wait for the Flask app to become available
        //             def maxRetries = 10
        //             def count = 0
        //             def ready = false

        //             while (count < maxRetries) {
        //                 def result = sh(script: "curl -s http://localhost:5000", returnStatus: true)
        //                 if (result == 0) {
        //                     ready = true
        //                     break
        //                 }
        //                 sleep 5
        //                 count++
        //             }

        //             if (!ready) {
        //                 error "App did not start in time."
        //             }
        //         }
        //     }
        // }

        // stage('Test Web App') {
        //     steps {
        //         sh 'curl -f http://localhost:5000'
        //     }
        // }
    }

    post {
        always {
            echo "Cleaning up containers"
            sh 'docker-compose down -v'
        }
    }
}
