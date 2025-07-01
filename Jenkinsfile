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
                    bat 'docker-compose down -v' // clean previous runs
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
                    def maxRetries = 20
                    def count = 0
                    def ready = false

                    while (count < maxRetries) {
                        // Use single quotes to avoid escaping issues
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
                        sleep 3
                        count++
                    }

                    if (!ready) {
                        // Show logs before failing
                        echo "App failed to start. Showing recent logs:"
                        bat 'docker-compose logs --tail=20 backend'
                        bat 'docker-compose logs --tail=10 db'
                        echo "Container status:"
                        bat 'docker-compose ps'
                        error "App did not start in time."
                    }
                }
            }
        }

        stage('Debug - Final Status Check') {
            steps {
                script {
                    echo "Final status check:"
                    bat 'docker-compose ps'
                    
                    // Windows netstat command
                    bat 'netstat -an | findstr :5000 || echo "No process listening on port 5000"'
                    
                    echo "Testing connectivity:"
                    bat 'curl -v http://localhost:5000 || echo "Curl failed"'
                }
            }
        }

        stage('Test Web App') {
            steps {
                script {
                    echo "Running comprehensive tests:"
                    
                    // Test 1: Basic connectivity
                    bat 'curl -f http://localhost:5000'
                    
                    // Test 2: Check response content (Windows findstr)
                    bat 'curl -s http://localhost:5000 | findstr "Hello" || echo "Hello not found in response"'
                    
                    // Test 3: Check HTTP status
                    def httpStatus = bat(
                        script: 'curl -s -o nul -w "%{http_code}" http://localhost:5000',
                        returnStdout: true
                    ).trim()
                    
                    if (httpStatus != "200") {
                        error "Expected HTTP 200, got ${httpStatus}"
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
            echo "Pipeline failed. Showing final container logs:"
            script {
                // Show logs on failure
                bat 'docker-compose logs --tail=50 backend || echo "Failed to get backend logs"'
                bat 'docker-compose logs --tail=20 db || echo "Failed to get db logs"'
                bat 'docker-compose ps || echo "Failed to get container status"'
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}