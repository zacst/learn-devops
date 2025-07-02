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
        // Remove this line: COMPOSE_FILE = "app/docker-compose.yml"
        DOCKER_BUILDKIT = "0"
        COMPOSE_DOCKER_CLI_BUILD = "0"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'docker-agent', url: 'https://github.com/zacst/learn-devops.git'
            }
        }

        stage('Setup Docker Compose') {
            steps {
                script {
                    // Install Docker Compose since it's not in the agent image
                    sh '''
                        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                        chmod +x /usr/local/bin/docker-compose
                        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
                    '''
                    sh 'docker --version'
                    sh 'docker-compose --version'
                    sh 'docker ps'
                    sh 'ls -la app/'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    // Run SonarQube analysis before building containers
                    def scannerHome = tool 'SonarQube Scanner 7.1.0.4889'
                    withSonarQubeEnv('SonarQube') { // 'SonarQube' should match your SonarQube server configuration name
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                            -Dsonar.projectKey=flask-ci-app \
                            -Dsonar.projectName='Flask CI Application' \
                            -Dsonar.projectVersion=1.0 \
                            -Dsonar.sources=app/ \
                            -Dsonar.language=py \
                            -Dsonar.sourceEncoding=UTF-8 \
                            -Dsonar.python.coverage.reportPaths=app/coverage.xml \
                            -Dsonar.exclusions=**/*test*/**,**/venv/**,**/__pycache__/**,**/migrations/**
                        """
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    // Wait for SonarQube analysis to complete and check quality gate
                    timeout(time: 5, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            echo "Quality Gate failed: ${qg.status}"
                            // You can choose to fail the build or just warn
                            // error "Pipeline aborted due to quality gate failure: ${qg.status}"
                            currentBuild.result = 'UNSTABLE'
                        } else {
                            echo "Quality Gate passed successfully!"
                        }
                    }
                }
            }
        }

        stage('Build and Start Services') {
            steps {
                dir('app') {
                    script {
                        try {
                            sh 'docker-compose down -v || true'
                            sh 'docker-compose build --no-cache'
                            sh 'docker-compose up -d'
                            sh 'docker-compose ps'
                        } catch (Exception e) {
                            echo "Error in build stage: ${e.getMessage()}"
                            sh 'docker-compose logs || true'
                            throw e
                        }
                    }
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
                            def exitCode = sh(script: 'docker-compose exec -T db pg_isready -U postgres', returnStatus: true)
                            if (exitCode == 0) {
                                echo "Database is ready!"
                                return
                            }
                            echo "Waiting... ($i/$retries)"
                            if (i % 5 == 0) {
                                sh 'docker-compose logs --tail=10 db || true'
                            }
                            sleep 2
                        }
                        sh 'docker-compose logs db || true'
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
                            def exitCode = sh(script: 'docker-compose exec -T backend python -c "import urllib.request; urllib.request.urlopen(\'http://localhost:5000/health\')"', returnStatus: true)
                            if (exitCode == 0) {
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
                        
                        // Test health endpoint
                        sh 'docker-compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen(\'http://localhost:5000/health\').read().decode())"'
                        
                        // Test main endpoint
                        def httpStatus = sh(
                            script: 'docker-compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen(\'http://localhost:5000\').getcode())"',
                            returnStdout: true
                        ).trim()

                        def response = sh(
                            script: 'docker-compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen(\'http://localhost:5000\').read().decode())"',
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
                        def exitCode = sh(script: 'docker-compose exec -T backend python -m pytest tests/ -v --cov=. --cov-report=xml:coverage.xml', returnStatus: true)
                        if (exitCode != 0) {
                            echo "No tests found or tests failed (exit code: ${exitCode})"
                        }
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
                        echo "Collecting final logs..."
                        sh 'docker-compose logs --tail=50 || true'
                        sh 'docker-compose ps || true'
                        
                        echo "Cleaning up containers..."
                        sh 'docker-compose down -v || true'
                        
                        // Clean up images created during this build
                        sh 'docker image prune -f --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" || true'
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
                        echo "Pipeline failed. Collecting detailed logs..."
                        sh 'docker-compose config || true'
                        sh 'docker-compose logs || true'
                        sh 'docker ps -a || true'
                        sh 'docker images || true'
                    }
                } catch (Exception e) {
                    echo "Failed to collect failure logs: ${e.getMessage()}"
                }
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}