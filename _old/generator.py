import streamlit as st
import ollama
import os
import io
from pathlib import Path

# --- 1. Page Configuration & Setup ---
st.set_page_config(page_title="AI DevSecOps Omni-Architect", layout="wide", page_icon="🛡️")

# File extensions for application detection (Includes C/C++ support)
EXT_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', 
    '.go': 'Go', '.java': 'Java', '.rs': 'Rust', '.php': 'PHP',
    '.c': 'C', '.cpp': 'C++', '.h': 'C/C++ Header', '.hpp': 'C++ Header'
}

# Cloud Provider Configuration for K8s and Terraform
CLOUD_CONFIG = {
    "Minikube": {"type": "local", "tf_provider": "kubernetes", "hints": "Use NodePort & config_path='~/.kube/config'"},
    "Kind": {"type": "local", "tf_provider": "kubernetes", "hints": "Use extraPortMappings and local-path storage."},
    "AWS (EKS)": {"type": "cloud", "tf_provider": "aws", "hints": "Use 'aws_eks_cluster' and VPC modules."},
    "Azure (AKS)": {"type": "cloud", "tf_provider": "azurerm", "hints": "Use 'azurerm_kubernetes_cluster' and Managed Identities."},
    "Google (GKE)": {"type": "cloud", "tf_provider": "google", "hints": "Use 'google_container_cluster' with Workload Identity."},
    "IBM (IKS)": {"type": "cloud", "tf_provider": "ibm", "hints": "Use IBM Container Registry and VPC Load Balancers."}
}

# --- 2. AI Engine & Robust Model Fetching ---
def get_installed_models():
    """Fetches local Ollama models with cross-version compatibility."""
    try:
        model_data = ollama.list()
        models_list = model_data.models if hasattr(model_data, 'models') else model_data.get('models', [])
        names = []
        for m in models_list:
            if hasattr(m, 'model'): names.append(m.model)
            elif isinstance(m, dict): names.append(m.get('model') or m.get('name'))
        return sorted(names) if names else ["llama3.2"]
    except:
        return ["llama3.2"]

def ask_ollama(model, prompt):
    """Execution engine for local LLM prompts."""
    try:
        with st.spinner(f"🤖 {model} is processing..."):
            response = ollama.generate(model=model, prompt=prompt)
            return response['response']
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

# --- 3. Sidebar: Filesystem Navigation ---
with st.sidebar:
    st.header("⚙️ Settings")
    available_models = get_installed_models()
    selected_model = st.selectbox("LLM Brain:", available_models)
    if st.button("🔄 Refresh Models"): st.rerun()

    st.divider()
    st.header("📂 Project Explorer")
    if 'current_path' not in st.session_state: st.session_state.current_path = os.getcwd()

    c1, c2 = st.columns(2)
    if c1.button("⬅️ Parent"):
        st.session_state.current_path = str(Path(st.session_state.current_path).parent)
        st.rerun()
    if c2.button("🏠 Home"):
        st.session_state.current_path = os.getcwd()
        st.rerun()

    st.caption(f"Path: `{st.session_state.current_path}`")
    
    try:
        items = os.listdir(st.session_state.current_path)
        folders = sorted([f for f in items if os.path.isdir(os.path.join(st.session_state.current_path, f)) and not f.startswith('.')])
        files = sorted([f for f in items if os.path.isfile(os.path.join(st.session_state.current_path, f)) and Path(f).suffix in EXT_MAP])
        
        target = st.selectbox("Navigate folder:", ["-- Stay Here --"] + folders)
        if target != "-- Stay Here --":
            st.session_state.current_path = os.path.join(st.session_state.current_path, target)
            st.rerun()

        selected_apps = st.multiselect("🎯 Select Source Files:", files)
    except Exception as e:
        st.error(f"Access Error: {e}")
        selected_apps = []

# --- 4. Main UI Flow ---
if not selected_apps:
    st.title("🛡️ AI DevSecOps Omni-Architect")
    st.info("👈 Use the sidebar to select your code (Python, C++, Go, etc.) and begin.")
    st.markdown("""
    ### System Capabilities:
    * **Standalone Docker**: Dedicated simple Dockerfile generation.
    * **Multi-Stage Native Builds**: Optimized for C/C++ and Go binaries.
    * **Cloud Provisioning**: Terraform (HCL) for cluster setup.
    * **OTel Insights**: Universal sidecar or SDK-based observability.
    * **Security Auditing**: CIS Benchmark compliance scanning.
    """)
else:
    st.title(f"🚀 Project: {', '.join(selected_apps)}")
    target_env = st.selectbox("Target Provider Environment:", list(CLOUD_CONFIG.keys()))
    
    tabs = st.tabs(["🐳 Infra (Docker/K8s)", "🌍 IaC (Terraform)", "🔭 Observability (OTel)", "🛡️ Compliance Audit", "📖 Docs"])

    with tabs[0]: # INFRASTRUCTURE
        st.subheader("Containerization & Deployment")
        # Restored the Simple Dockerfile option
        sub_infra = st.radio("Output Level:", ["Simple Dockerfile", "Docker Compose", "Kubernetes Manifests"], horizontal=True)
        
        if st.button(f"Generate {sub_infra}", type="primary"):
            mode_map = {
                "Simple Dockerfile": "Generate only a standalone Multi-stage Dockerfile.",
                "Docker Compose": "Generate a Multi-stage Dockerfile and a docker-compose.yml.",
                "Kubernetes Manifests": "Generate a Multi-stage Dockerfile and K8s Deployment, Service, and HPA YAMLs."
            }
            prompt = f"As a Senior SRE, {mode_map[sub_infra]} for {selected_apps} targeting {target_env}. Use '---FILE: filename---' markers for each file."
            st.session_state['infra_res'] = ask_ollama(selected_model, prompt)
        
        if 'infra_res' in st.session_state:
            for part in st.session_state['infra_res'].split('---FILE:')[1:]:
                try:
                    fname, code = part.strip().split('\n', 1)
                    with st.container(border=True):
                        st.subheader(f"📄 {fname}")
                        st.download_button("📥 Download", code, file_name=fname.strip(), key=f"dl_{fname}")
                        st.code(code, language='yaml' if '.yaml' in fname or '.yml' in fname else 'dockerfile')
                except: continue

    with tabs[1]: # TERRAFORM
        st.subheader(f"Terraform (HCL) for {target_env}")
        if st.button("🏗️ Generate HCL Infrastructure"):
            tf_prov = CLOUD_CONFIG[target_env]['tf_provider']
            hints = CLOUD_CONFIG[target_env]['hints']
            prompt = f"Generate Terraform code (main.tf, variables.tf, outputs.tf) for {target_env} using '{tf_prov}'. Context: {hints}. Separate with '---FILE: filename---'."
            st.session_state['tf_res'] = ask_ollama(selected_model, prompt)

        if 'tf_res' in st.session_state:
            for part in st.session_state['tf_res'].split('---FILE:')[1:]:
                try:
                    fname, code = part.strip().split('\n', 1)
                    with st.container(border=True):
                        st.subheader(f"📜 {fname}")
                        st.download_button("📥 Download HCL", code, file_name=fname.strip(), key=f"tf_dl_{fname}")
                        st.code(code, language='hcl')
                except: continue

    with tabs[2]: # OBSERVABILITY (OTEL)
        st.subheader("OpenTelemetry Monitoring Strategy")
        otel_mode = st.radio("Approach:", ["Universal Sidecar (K8s)", "SDK Implementation (Code)"], horizontal=True)
        if st.button("🚀 Generate OTel Config"):
            if otel_mode == "Universal Sidecar (K8s)":
                prompt = f"Generate a K8s Deployment YAML for {selected_apps} with an OpenTelemetry Collector sidecar and ConfigMap."
            else:
                prompt = f"Provide code-level OpenTelemetry SDK implementation for {selected_apps} to export traces and metrics."
            st.session_state['otel_res'] = ask_ollama(selected_model, prompt)
        if 'otel_res' in st.session_state:
            st.markdown(st.session_state['otel_res'])

    with tabs[3]: # COMPLIANCE AUDIT
        st.subheader("🛡️ Security & CIS Compliance Scan")
        audit_level = st.selectbox("Compliance Standard:", ["CIS Benchmark Compliance", "SOC2 Readiness", "Standard SRE Audit"])
        if st.button("🔍 Run Audit"):
            infra_ctx = st.session_state.get('infra_res', '')
            tf_ctx = st.session_state.get('tf_res', '')
            if not infra_ctx and not tf_ctx:
                st.warning("Generate Infrastructure or Terraform first to audit the configuration.")
            else:
                prompt = f"Act as a DevSecOps Auditor. Review the following code against {audit_level} for {target_env}: \n{infra_ctx}\n{tf_ctx}"
                st.markdown(ask_ollama(selected_model, prompt))

    with tabs[4]: # DOCS
        if st.button("📝 Generate README & Runbook"):
            st.markdown(ask_ollama(selected_model, f"Create a README.md and SRE Runbook for {selected_apps} on {target_env}."))