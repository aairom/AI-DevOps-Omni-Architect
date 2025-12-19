# 🛡️ DevSecOps Omni-Architect v41.0

Omni-Architect is a high-performance, AI-native workbench designed to automate the entire lifecycle of cloud-native infrastructure. This version introduces a **Visual Navigation** model, allowing for precise context selection and enterprise-grade infrastructure targeting.

**Note: Local features and Multi-Provider LLM integration are fully tested. Cloud provisioning and OTel capacities are active in this version.**

------

## 🚀 Key Features

### 🏗️ Precision Infrastructure & Orchestration

- **Visual Folder Explorer**: Navigate local directories with dedicated "Up" and "Home" controls.
- **Smart Filter Helper**: Automatically highlights application code in **C, Go, PHP, JS, Java, and Bash** while keeping all files visible for selection.
- **Granular Cloud Flavors**: Explicit generation targets for **IBM (IKS), Google (GKE), AWS (EKS), Azure (AKS)**, and local tools like **Minikube** and **Kind**.

### 🔭 Observability-as-Code

- **OTel Sidecar Injection**: Mutate manifests to include OpenTelemetry collectors.
- **Monitoring Stack**: Generates `otel-collector.yaml`, Prometheus rules, and Grafana dashboards.

### 🛡️ Security & FinOps Shield

- **Hardening**: Injects non-root users, read-only filesystems, and security contexts.
- **FinOps Optimization**: AI-driven analysis to set CPU/Memory requests and cloud cost limits.

### 🤖 Multi-Model Brains

- **Dynamic Ollama Discovery**: Automatic detection of local LLMs with manual override fallback.
- **Enterprise Integration**: Full support for **IBM watsonx (Granite)**, **OpenAI (GPT-4o)**, and **Google (Gemini 1.5 Flash)**.

------

## 🛠️ Setup & Installation

### 1. Environment Configuration

Create a `.env` file in the root directory to store your enterprise credentials. The application will automatically detect and load these on startup.

```.env
# IBM watsonx
WATSONX_API_KEY=your_key_here
WATSONX_PROJECT_ID=your_project_id_here

# Google
GEMINI_API_KEY=your_key_here

# OpenAI
OPENAI_API_KEY=your_key_here
```

### 2. Local Execution



```bash
# Install dependencies
pip install -r requirements.txt

# Launch the Architect
streamlit run ai-devops-Omni-Architect_vxx.py
```

### 3. Containerized Deployment (Recommended)

This method ensures all CLI tools (Git, Curl) and Python environments are perfectly synced.



```bash
# Build and launch the container
docker-compose up --build -d

# Access the UI
http://localhost:8501
```

------

## 🕹️ How to Use

1. **Select Brain**: Choose your AI Provider (e.g., IBM watsonx) and Model in the sidebar.
2. **Visual Navigation**: Use the Explorer to navigate to your project folder.
3. **Smart Select**: Toggle the **"Smart Filter"** to highlight code files while keeping configuration files visible.
4. **Build Infra**: Select your **Strategy** (e.g., K8s Manifests) and **Flavor** (e.g., IBM IKS), then click **Generate**.
5. **Observe**: Go to the **Observability** tab to inject an OTel sidecar into your new manifest.
6. **Secure**: Use the **Security** tab to harden the generated code.
7. **Deploy**: From the **Execution** tab, use the integrated Download Buttons or run CLI commands directly.

------

## 🔒 Security Policy

Omni-Architect follows "Zero Trust" infrastructure principles. Generated code defaults to:

- Non-privileged container execution.
- Read-only root filesystems where applicable.
- Resource limits and quotas definition.