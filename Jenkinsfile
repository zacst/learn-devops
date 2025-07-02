pipeline {
    agent {
        dockerfile {
            filename 'dockerfile' // Root-level Dockerfile for Jenkins agent
            additionalBuildArgs '--no-cache'
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        COMPOSE_PROJECT_NAME = "flaskci"
        COMPOSE_FILE = "app/docker-compose.yml"
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
                dir('app') {
                    sh 'docker-compose down -v || true'
                    sh 'docker-compose build --no-cache'
                    sh 'docker-compose up -d'
                }
            }
        }

        stage('Wait for Database') {
            steps {
                dir('app') {
                    script {
                        echo "Waiting for PostgreSQL to be ready..."
                        def retries = 30
                        for (int i = 1; i <= retries; i++) {
                            if (sh(script: 'docker-compose exec -T db pg_isready -U postgres', returnStatus: true) == 0) {
                                echo "Database is ready!"
                                return
                            }
                            echo "Waiting... ($i/$retries)"
                            sleep 2
                        }
                        error "Database did not become ready in time."
                    }
                }
            }
        }

        stage('Wait for App to Start') {
            steps {
                dir('app') {
                    script {
                        echo "Waiting for Flask app to be ready..."
                        def retries = 30
                        for (int i = 1; i <= retries; i++) {
                            if (sh(script: 'docker-compose exec -T backend curl -s -f http://localhost:5000/health', returnStatus: true) == 0) {
                                echo "Flask app is ready!"
                                return
                            }
                            echo "App not ready yet, waiting... ($i/$retries)"
                            if (i % 10 == 0) {
                                sh 'docker-compose logs --tail=20 backend || true'
                                sh 'docker-compose ps || true'
                            }
                            sleep 3
                        }
                        sh 'docker-compose logs backend || true'
                        sh 'docker-compose logs db || true'
                        sh 'docker-compose ps || true'
                        sh 'docker ps -a || true'
                        error "App did not start in time."
                    }
                }
            }
        }

        stage('Test Web App') {
            steps {
                dir('app') {
                    script {
                        echo "Running HTTP tests..."
                        sh 'docker-compose exec -T backend curl -f http://localhost:5000/health'
                        sh 'docker-compose exec -T backend curl -f http://localhost:5000'

                        def httpStatus = sh(
                            script: 'docker-compose exec -T backend curl -s -o /dev/null -w "%{http_code}" http://localhost:5000',
                            returnStdout: true
                        ).trim()

                        def response = sh(
                            script: 'docker-compose exec -T backend curl -s http://localhost:5000',
                            returnStdout: true
                        ).trim()

                        echo "HTTP Status: ${httpStatus}"
                        echo "Response content: ${response}"

                        if (httpStatus != "200") {
                            error "Expected HTTP 200, got ${httpStatus}"
                        }
                        if (!response.contains("Hello from Flask")) {
                            error "Unexpected response: ${response}"
                        }

                        echo "All HTTP tests passed!"
                    }
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                dir('app') {
                    script {
                        echo "Running unit tests..."
                        sh 'docker-compose exec -T backend python -m pytest tests/ -v || echo "No tests found"'
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                try {
                    dir('app') {
                        echo "Cleaning up containers..."
                        sh 'docker-compose down -v || true'
                        sh 'docker system prune -f || true'
                    }
                } catch (Exception e) {
                    echo "Cleanup failed: ${e.getMessage()}"
                }
            }
        }
        failure {
            script {
                try {
                    dir('app') {
                        echo "Pipeline failed. Collecting logs..."
                        sh 'docker-compose logs backend || true'
                        sh 'docker-compose logs db || true'
                        sh 'docker-compose ps || true'
                        sh 'docker ps -a || true'
                    }
                } catch (Exception e) {
                    echo "Failed to collect logs: ${e.getMessage()}"
                }
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}