# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Git and networking
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Ensure your requirements.txt includes: streamlit, ollama, google-generativeai, requests, python-dotenv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "ai-devops-Omni-Architect_v40.py", "--server.address=0.0.0.0"]