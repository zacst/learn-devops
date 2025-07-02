# app/Dockerfile - Flask Application Dockerfile
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]