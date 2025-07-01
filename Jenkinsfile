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

        stage('Build and Start Services') {
            steps {
                script {
                    bat 'docker-compose down -v'
                    bat 'docker-compose build'
                    bat 'docker-compose up -d'
                }
            }
        }

        stage('Wait for Database') {
            steps {
                script {
                    echo "Waiting for PostgreSQL to be ready..."
                    def maxRetries = 30
                    def count = 0
                    def dbReady = false

                    while (count < maxRetries) {
                        def result = bat(
                            script: 'docker-compose exec -T db pg_isready -U postgres',
                            returnStatus: true
                        )
                        if (result == 0) {
                            dbReady = true
                            echo "Database is ready!"
                            break
                        }
                        echo "Database not ready yet, waiting... (${count + 1}/${maxRetries})"
                        sleep 2
                        count++
                    }

                    if (!dbReady) {
                        error "Database did not become ready in time."
                    }
                }
            }
        }

        stage('Wait for App to Start') {
            steps {
                script {
                    echo "Waiting for Flask app to be ready..."
                    def maxRetries = 30
                    def count = 0
                    def ready = false

                    while (count < maxRetries) {
                        // Test from host machine only (not inside container)
                        def result = bat(
                            script: 'curl -s -f http://localhost:5000',
                            returnStatus: true
                        )
                        if (result == 0) {
                            ready = true
                            echo "Flask app is ready!"
                            break
                        }
                        echo "App not ready yet, waiting... (${count + 1}/${maxRetries})"
                        
                        // Show logs every 10 attempts
                        if (count % 10 == 0 && count > 0) {
                            echo "App logs (last 20 lines):"
                            bat 'docker-compose logs --tail=20 backend'
                            echo "Container status:"
                            bat 'docker-compose ps'
                        }
                        
                        sleep 3
                        count++
                    }

                    if (!ready) {
                        echo "App failed to start. Final diagnostics:"
                        bat 'docker-compose logs backend'
                        bat 'docker-compose logs db'
                        bat 'docker-compose ps'
                        bat 'netstat -an | findstr :5000 || echo "No process listening on port 5000"'
                        error "App did not start in time."
                    }
                }
            }
        }

        stage('Test Web App') {
            steps {
                script {
                    echo "Running tests:"
                    
                    // Test basic connectivity
                    bat 'curl -f http://localhost:5000'
                    
                    // Get HTTP status code
                    def httpStatus = bat(
                        script: 'curl -s -o NUL -w "%{http_code}" http://localhost:5000',
                        returnStdout: true
                    ).trim()
                    
                    echo "HTTP Status Code: ${httpStatus}"
                    
                    // Get response content
                    def response = bat(
                        script: 'curl -s http://localhost:5000',
                        returnStdout: true
                    ).trim()
                    
                    echo "Response content: ${response}"
                    
                    // Validate HTTP status
                    if (httpStatus != "200") {
                        error "Expected HTTP 200, got ${httpStatus}"
                    }
                    
                    // Validate response content contains expected text
                    if (!response.contains("Hello from Flask")) {
                        error "Response does not contain expected content. Got: ${response}"
                    }
                    
                    echo "All tests passed! HTTP Status: ${httpStatus}"
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning up containers"
            bat 'docker-compose down -v'
        }
        failure {
            echo "Pipeline failed. Final logs:"
            script {
                bat 'docker-compose logs backend || echo "Failed to get backend logs"'
                bat 'docker-compose logs db || echo "Failed to get db logs"'
                bat 'docker-compose ps || echo "Failed to get container status"'
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}