# Set base image
FROM jenkins/jenkins:lts-jdk21

# Switch to root to install dependencies
USER root

# Install Docker CLI
RUN apt-get update && \
    apt-get install -y lsb-release curl gnupg && \
    curl -fsSLo /usr/share/keyrings/docker-archive-keyring.asc https://download.docker.com/linux/debian/gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.asc] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-compose-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the Jenkins user
USER jenkins

# Install Jenkins plugins (latest versions by default)
RUN jenkins-plugin-cli --plugins \
    "blueocean docker-workflow"