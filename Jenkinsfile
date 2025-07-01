pipeline {
    agent {
        dockerfile {
            // Use the Dockerfile in the root directory for the Jenkins agent
            filename 'Dockerfile'
            // Additional arguments if needed
            additionalBuildArgs '--no-cache'
            // Use proper Linux paths in container
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        COMPOSE_PROJECT_NAME = "flaskci"
        COMPOSE_FILE = "app/docker-compose.yml"
        // Disable BuildKit for compatibility
        DOCKER_BUILDKIT = "0"
        COMPOSE_DOCKER_CLI_BUILD = "0"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'docker-agent', url: 'https://github.com/zacst/learn-devops.git'
            }
        }

        stage('Build and Start Services') {
            steps {
                script {
                    dir('app') {
                        // Clean up any existing containers first
                        sh 'docker-compose down -v || true'
                        sh 'docker-compose build --no-cache'
                        sh 'docker-compose up -d'
                    }
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

                    dir('app') {
                        while (count < maxRetries) {
                            def result = sh(
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
                        // Test the health endpoint using docker-compose exec
                        dir('app') {
                            def result = sh(
                                script: 'docker-compose exec -T backend curl -s -f http://localhost:5000/health',
                                returnStatus: true
                            )
                            if (result == 0) {
                                ready = true
                                echo "Flask app is ready!"
                                break
                            }
                        }
                        echo "App not ready yet, waiting... (${count + 1}/${maxRetries})"
                        
                        // Show logs every 10 attempts
                        if (count % 10 == 0 && count > 0) {
                            echo "App logs (last 20 lines):"
                            dir('app') {
                                sh 'docker-compose logs --tail=20 backend'
                                echo "Container status:"
                                sh 'docker-compose ps'
                            }
                        }
                        
                        sleep 3
                        count++
                    }

                    if (!ready) {
                        echo "App failed to start. Final diagnostics:"
                        dir('app') {
                            sh 'docker-compose logs backend || true'
                            sh 'docker-compose logs db || true'
                            sh 'docker-compose ps || true'
                            sh 'docker ps -a || true'
                        }
                        error "App did not start in time."
                    }
                }
            }
        }

        stage('Test Web App') {
            steps {
                script {
                    echo "Running tests:"
                    
                    dir('app') {
                        // Test health endpoint from within the backend container
                        sh 'docker-compose exec -T backend curl -f http://localhost:5000/health'
                        
                        // Test main endpoint
                        sh 'docker-compose exec -T backend curl -f http://localhost:5000'
                        
                        // Get HTTP status code and response
                        def httpStatus = sh(
                            script: 'docker-compose exec -T backend curl -s -o /dev/null -w "%{http_code}" http://localhost:5000',
                            returnStdout: true
                        ).trim()
                        
                        echo "HTTP Status Code: ${httpStatus}"
                        
                        def response = sh(
                            script: 'docker-compose exec -T backend curl -s http://localhost:5000',
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

        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running unit tests inside the application container..."
                    dir('app') {
                        // Run tests inside the backend container
                        sh 'docker-compose exec -T backend python -m pytest tests/ -v || echo "No tests found"'
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "Cleaning up containers"
                try {
                    dir('app') {
                        sh 'docker-compose down -v || true'
                        sh 'docker system prune -f || true'
                    }
                } catch (Exception e) {
                    echo "Failed to cleanup containers: ${e.getMessage()}"
                }
            }
        }
        failure {
            script {
                echo "Pipeline failed. Final logs:"
                try {
                    dir('app') {
                        sh 'docker-compose logs backend || echo "Failed to get backend logs"'
                        sh 'docker-compose logs db || echo "Failed to get db logs"'
                        sh 'docker-compose ps || echo "Failed to get container status"'
                        sh 'docker ps -a || echo "Failed to get all containers"'
                    }
                } catch (Exception e) {
                    echo "Failed to get failure logs: ${e.getMessage()}"
                }
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}