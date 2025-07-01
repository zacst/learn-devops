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

        stage('Wait for Services') {
            steps {
                script {
                    echo "Waiting for services to be healthy..."
                    def maxRetries = 60
                    def count = 0
                    def servicesReady = false

                    while (count < maxRetries) {
                        def result = bat(
                            script: 'docker-compose ps --services --filter "status=running" | findstr /C:"db backend"',
                            returnStatus: true
                        )
                        
                        // Check if both services are healthy
                        def healthCheck = bat(
                            script: 'docker-compose exec -T backend curl -f http://localhost:5000',
                            returnStatus: true
                        )
                        
                        if (result == 0 && healthCheck == 0) {
                            servicesReady = true
                            echo "All services are ready!"
                            break
                        }
                        echo "Services not ready yet, waiting... (${count + 1}/${maxRetries})"
                        
                        // Show container status every 10 attempts
                        if (count % 10 == 0) {
                            echo "Current container status:"
                            bat 'docker-compose ps'
                            echo "Backend logs (last 10 lines):"
                            bat 'docker-compose logs --tail=10 backend'
                        }
                        
                        sleep 5
                        count++
                    }

                    if (!servicesReady) {
                        echo "Services failed to start. Final diagnostics:"
                        bat 'docker-compose ps'
                        bat 'docker-compose logs backend'
                        bat 'docker-compose logs db'
                        error "Services did not become ready in time."
                    }
                }
            }
        }

        stage('Test Web App') {
            steps {
                script {
                    echo "Running comprehensive tests:"
                    
                    // Test 1: Test through docker-compose network
                    bat 'docker-compose exec -T backend curl -f http://localhost:5000'
                    
                    // Test 2: Test from host machine
                    bat 'curl -f http://localhost:5000'
                    
                    // Test 3: Check response content
                    def response = bat(
                        script: 'curl -s http://localhost:5000',
                        returnStdout: true
                    ).trim()
                    
                    echo "Response from app: ${response}"
                    
                    // Test 4: Verify it contains expected content
                    if (!response.contains("Hello") && !response.contains("DB")) {
                        error "Response doesn't contain expected content: ${response}"
                    }
                    
                    // Test 5: Check HTTP status
                    def httpStatus = bat(
                        script: 'curl -s -o nul -w "%{http_code}" http://localhost:5000',
                        returnStdout: true
                    ).trim()
                    
                    if (httpStatus != "200") {
                        error "Expected HTTP 200, got ${httpStatus}"
                    }
                    
                    echo "All tests passed! HTTP Status: ${httpStatus}"
                    echo "App response: ${response}"
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
            echo "Pipeline failed. Showing final diagnostics:"
            script {
                bat 'docker-compose logs backend || echo "Failed to get backend logs"'
                bat 'docker-compose logs db || echo "Failed to get db logs"'
                bat 'docker-compose ps || echo "Failed to get container status"'
                bat 'docker network ls || echo "Failed to get network info"'
                bat 'netstat -an | findstr :5000 || echo "No process listening on port 5000"'
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}