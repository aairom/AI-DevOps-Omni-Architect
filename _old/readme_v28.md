# 🛡️ Alpha version-DevSecOps Omni-Architect v27.0 (in progress)

Omni-Architect is a high-performance, AI-native workbench designed to automate the entire lifecycle of cloud-native infrastructure. From single-container Dockerfiles to complex multi-cloud Kubernetes manifests with integrated observability sidecars, this tool bridges the gap between AI generation and production deployment.

**Local features are tested, not the cloud features, nor Otel capacities**

## 🚀 Key Features

### 🏗️ Infrastructure & Orchestration

- **Multi-Flavor K8s:** Generate optimized manifests for **IKS, GKE, EKS, AKS, Minikube,** and **Kind**.
- **Strategy Toggle:** Instantly switch between **Single Dockerfiles**, **Docker Compose** stacks, or full **Kubernetes** deployments.
- **One-Click Hardening:** Automatically mutate manifests to include non-root users, security contexts, and pinned image versions.

### 🔭 Observability-as-Code

- **Sidecar Injection:** Automatically inject **OpenTelemetry (OTel)** collectors into existing K8s Pod specs.
- **Full Stack Monitoring:** Generates `otel-collector.yaml`, **Prometheus** alerting rules, and **Grafana** JSON dashboards in seconds.

### 🤖 Enterprise AI Integration (Multi-Model)

- **Local-First:** Native support for **Ollama** (Llama 3.2, etc.) for air-gapped environments.
- **LLM Platforms and Providers:** Integrated support for **IBM watsonx** (including Granite models), **OpenAI (GPT-4o)**, **Google (Gemini 1.5 Flash)**.
- **IBM IAM Token Exchange:** Automatic handling of IBM Cloud IAM authentication for enterprise WatsonX instances.

------

## 🛠️ Setup & Installation

### 1. Environment Configuration

Create a `.env` file in the root directory to store your enterprise credentials. The application will automatically detect and load these on startup.

Code snippet

```
# IBM watsonx
WATSONX_API_KEY=your_key_here
WATSONX_PROJECT_ID=your_project_id_here

# Google
GEMINI_API_KEY=your_key_here

# OpenAI
OPENAI_API_KEY=your_key_here
```

### 2. Local Execution

```
# Install dependencies
pip install -r requirements.txt

# Launch the Architect
streamlit run ai-devops-Omni-Architect.py
```

### 3. Containerized Deployment

Run the entire workbench inside Docker to ensure consistent CLI tooling (includes `kubectl` and `git`).

```
docker-compose up --build -d
```

------

## 🕹️ How to Use

1. **Select Brain:** Choose your AI Provider (e.g., IBM watsonx) in the sidebar.
2. **Context Loading:** Select the source code files you want the AI to analyze.
3. **Build:** Navigate to the **Infra** tab, select your K8s flavor, and click Generate.
4. **Observe:** Go to the **Observability** tab to inject an OTel sidecar into your new manifest.
5. **Secure:** Use the **Security Shield** to harden the generated code.
6. **Deploy:** From the **Execution** tab, commit your changes to Git and run `kubectl apply` directly.

------

## 🔒 Security Policy

Omni-Architect follows "Zero Trust" infrastructure principles. Generated code defaults to:

- Non-privileged container execution.
- Read-only root filesystems where applicable.
- Resource limits and quotas definition.

⛓️ CI/CD Integration
Omni-Architect now generates automated workflows to ensure your security and observability configurations are applied consistently.

Generated Workflow Stages:
Static Analysis: Scans the generated Terraform/K8s files using Checkov/KICS.

Container Audit: Runs Trivy against the generated Dockerfile.

Observability Check: Validates OTel collector configurations.

Deployment: Applies manifests to the selected K8s flavor (GKE/EKS/IKS).

GitHub Actions Example:
To use the generated pipeline, save it as .github/workflows/deploy.yml. Ensure you have set your KUBE_CONFIG secrets in GitHub to match the flavor you selected in the Architect.

🛡️ Why OPA Governance is the Final Piece
By adding Policy-as-Code, you move from just "building" secure things to "enforcing" security.

Compliance: Automatically ensure every generated manifest meets SOC2 or HIPAA standards.

Safety: Even if a user manually changes a Dockerfile to use root, the cluster will reject it.

Consistency: All developers across your GKE, EKS, or IKS clusters must follow the same rules.