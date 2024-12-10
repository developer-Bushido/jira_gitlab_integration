# Use a Python base image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install ping utility and other debugging tools
RUN apt-get update && apt-get install -y \
    curl \
    dnsutils \
    iputils-ping \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
    python-gitlab \
    jira

# Copy all the Python modules and the main script into the container
COPY . /app/

# Command to run the application
CMD ["python", "main.py"]