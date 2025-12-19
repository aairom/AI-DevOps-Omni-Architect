FROM python:3.11-slim

# Install system dependencies for DevSecOps tasks
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "ai-devops-Omni-Architect.py", "--server.port=8501", "--server.address=0.0.0.0"]