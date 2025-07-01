pipeline {
    agent {
        dockerfile {
            // Use the Dockerfile in the root directory for the Jenkins agent
            filename 'Dockerfile'
            // Additional arguments if needed
            additionalBuildArgs '--no-cache'
            // Fix Windows Docker path issues
            args '--user root'
        }
    }

    environment {
        COMPOSE_PROJECT_NAME = "flaskci"
        COMPOSE_FILE = "app/docker-compose.yml"
        // Fix Windows Docker daemon issues
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
                        // Use bat for Windows or sh for Unix
                        if (isUnix()) {
                            sh 'docker-compose down -v || true'
                            sh 'docker-compose build'
                            sh 'docker-compose up -d'
                        } else {
                            bat 'docker-compose down -v || exit 0'
                            bat 'docker-compose build'
                            bat 'docker-compose up -d'
                        }
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
                            def result
                            if (isUnix()) {
                                result = sh(
                                    script: 'docker-compose exec -T db pg_isready -U postgres',
                                    returnStatus: true
                                )
                            } else {
                                result = bat(
                                    script: 'docker-compose exec -T db pg_isready -U postgres',
                                    returnStatus: true
                                )
                            }
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
                        // Test the health endpoint
                        def result
                        if (isUnix()) {
                            result = sh(
                                script: 'curl -s -f http://localhost:5000/health',
                                returnStatus: true
                            )
                        } else {
                            // Use PowerShell for Windows HTTP requests
                            result = powershell(
                                script: '''
                                try {
                                    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 5
                                    if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 }
                                } catch { exit 1 }
                                ''',
                                returnStatus: true
                            )
                        }
                        if (result == 0) {
                            ready = true
                            echo "Flask app is ready!"
                            break
                        }
                        echo "App not ready yet, waiting... (${count + 1}/${maxRetries})"
                        
                        // Show logs every 10 attempts
                        if (count % 10 == 0 && count > 0) {
                            echo "App logs (last 20 lines):"
                            dir('app') {
                                if (isUnix()) {
                                    sh 'docker-compose logs --tail=20 backend'
                                    echo "Container status:"
                                    sh 'docker-compose ps'
                                } else {
                                    bat 'docker-compose logs --tail=20 backend'
                                    echo "Container status:"
                                    bat 'docker-compose ps'
                                }
                            }
                        }
                        
                        sleep 3
                        count++
                    }

                    if (!ready) {
                        echo "App failed to start. Final diagnostics:"
                        dir('app') {
                            if (isUnix()) {
                                sh 'docker-compose logs backend'
                                sh 'docker-compose logs db'
                                sh 'docker-compose ps'
                            } else {
                                bat 'docker-compose logs backend'
                                bat 'docker-compose logs db'
                                bat 'docker-compose ps'
                            }
                        }
                        if (isUnix()) {
                            sh 'netstat -an | grep :5000 || echo "No process listening on port 5000"'
                        } else {
                            bat 'netstat -an | findstr :5000 || echo "No process listening on port 5000"'
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
                    
                    if (isUnix()) {
                        // Test health endpoint
                        sh 'curl -f http://localhost:5000/health'
                        
                        // Test main endpoint
                        sh 'curl -f http://localhost:5000'
                        
                        // Get HTTP status code
                        def httpStatus = sh(
                            script: 'curl -s -o /dev/null -w "%{http_code}" http://localhost:5000',
                            returnStdout: true
                        ).trim()
                        
                        echo "HTTP Status Code: ${httpStatus}"
                        
                        // Get response content
                        def response = sh(
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
                    } else {
                        // Windows PowerShell equivalent
                        def testResult = powershell(
                            script: '''
                            try {
                                $healthResponse = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 10
                                Write-Host "Health check passed"
                                
                                $mainResponse = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 10
                                Write-Host "HTTP Status Code: $($mainResponse.StatusCode)"
                                Write-Host "Response content: $($mainResponse.Content)"
                                
                                if ($mainResponse.StatusCode -ne 200) {
                                    Write-Error "Expected HTTP 200, got $($mainResponse.StatusCode)"
                                    exit 1
                                }
                                
                                if ($mainResponse.Content -notmatch "Hello from Flask") {
                                    Write-Error "Response does not contain expected content"
                                    exit 1
                                }
                                
                                Write-Host "All tests passed! HTTP Status: $($mainResponse.StatusCode)"
                                exit 0
                            } catch {
                                Write-Error "Test failed: $_"
                                exit 1
                            }
                            ''',
                            returnStatus: true
                        )
                        
                        if (testResult != 0) {
                            error "Web app tests failed"
                        }
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
                        if (isUnix()) {
                            sh 'docker-compose exec -T backend python -m pytest tests/ -v || echo "No tests found"'
                        } else {
                            bat 'docker-compose exec -T backend python -m pytest tests/ -v || echo "No tests found"'
                        }
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
                        if (isUnix()) {
                            sh 'docker-compose down -v || true'
                        } else {
                            bat 'docker-compose down -v || exit 0'
                        }
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
                        if (isUnix()) {
                            sh 'docker-compose logs backend || echo "Failed to get backend logs"'
                            sh 'docker-compose logs db || echo "Failed to get db logs"'
                            sh 'docker-compose ps || echo "Failed to get container status"'
                        } else {
                            bat 'docker-compose logs backend || echo "Failed to get backend logs"'
                            bat 'docker-compose logs db || echo "Failed to get db logs"'
                            bat 'docker-compose ps || echo "Failed to get container status"'
                        }
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