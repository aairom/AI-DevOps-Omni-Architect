import streamlit as st
import ollama
import os
from pathlib import Path

# --- 1. Page Configuration ---
st.set_page_config(page_title="AI DevSecOps Omni-Architect", layout="wide", page_icon="🛡️")

EXT_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', 
    '.go': 'Go', '.java': 'Java', '.rs': 'Rust', '.php': 'PHP',
    '.c': 'C', '.cpp': 'C++', '.h': 'C/C++ Header', '.hpp': 'C++ Header'
}

CLOUD_CONFIG = {
    "Minikube": {"type": "local", "tf_provider": "kubernetes", "hints": "Use NodePort"},
    "AWS (EKS)": {"type": "cloud", "tf_provider": "aws", "hints": "Use EKS modules"},
    "Azure (AKS)": {"type": "cloud", "tf_provider": "azurerm", "hints": "Use AKS cluster resource"},
    "Google (GKE)": {"type": "cloud", "tf_provider": "google", "hints": "Use GKE standard"},
    "IBM (IKS)": {"type": "cloud", "tf_provider": "ibm", "hints": "Use VPC Load Balancers"}
}

# --- 2. Logic & AI Helpers ---
def get_installed_models():
    try:
        model_data = ollama.list()
        models_list = model_data.models if hasattr(model_data, 'models') else model_data.get('models', [])
        names = [m.model if hasattr(m, 'model') else m.get('model', m.get('name')) for m in models_list]
        return sorted(names) if names else ["llama3.2"]
    except:
        return ["llama3.2"]

def ask_ollama(model, prompt):
    try:
        with st.spinner(f"🤖 {model} is architecting..."):
            res = ollama.generate(model=model, prompt=prompt)
            return res['response']
    except Exception as e:
        return f"Error: {str(e)}"

# --- 3. Enhanced File Browser Dialog ---
@st.dialog("📂 Project File Navigator", width="large")
def file_browser_dialog():
    st.markdown("### 🔍 Filter & Select Files")
    c1, c2, c3 = st.columns([1, 1, 5])
    if c1.button("⬅️ Back"):
        st.session_state.current_path = str(Path(st.session_state.current_path).parent)
        st.rerun()
    if c2.button("🏠 Home"):
        st.session_state.current_path = os.getcwd()
        st.rerun()
    st.info(f"📍 `{st.session_state.current_path}`")
    search_query = st.text_input("Search files...", placeholder="e.g. main.cpp").lower()

    try:
        items = os.listdir(st.session_state.current_path)
        folders = sorted([f for f in items if os.path.isdir(os.path.join(st.session_state.current_path, f)) and not f.startswith('.')])
        files = sorted([f for f in items if os.path.isfile(os.path.join(st.session_state.current_path, f)) and Path(f).suffix in EXT_MAP])
        filtered_files = [f for f in files if search_query in f.lower()]
        col_folders, col_files = st.columns([1, 2])

        with col_folders:
            st.subheader("📁 Folders")
            for folder in folders:
                if st.button(f" {folder}", key=f"btn_{folder}", use_container_width=True):
                    st.session_state.current_path = os.path.join(st.session_state.current_path, folder)
                    st.rerun()

        with col_files:
            st.subheader("📄 Files")
            if filtered_files:
                for file in filtered_files:
                    is_checked = file in st.session_state.selected_apps
                    if st.checkbox(file, value=is_checked, key=f"chk_{file}"):
                        if file not in st.session_state.selected_apps: st.session_state.selected_apps.append(file)
                    else:
                        if file in st.session_state.selected_apps: st.session_state.selected_apps.remove(file)
            else: st.write("No matching files.")
        
        st.divider()
        if st.button("💾 Save Selection & Close", type="primary", use_container_width=True):
            st.rerun()
    except Exception as e: st.error(f"Error: {e}")

# --- 4. Sidebar & State Initialization ---
if 'current_path' not in st.session_state: st.session_state.current_path = os.getcwd()
if 'selected_apps' not in st.session_state: st.session_state.selected_apps = []

with st.sidebar:
    st.header("⚙️ Configuration")
    selected_model = st.selectbox("LLM Brain:", get_installed_models())
    if st.button("🔍 Open File Browser", use_container_width=True): file_browser_dialog()
    if st.session_state.selected_apps:
        st.success(f"Selected: {len(st.session_state.selected_apps)}")
        if st.button("🗑️ Clear All"):
            st.session_state.selected_apps = []
            st.rerun()
    else: st.warning("No files selected.")

# --- 5. Main UI Logic ---
if not st.session_state.selected_apps:
    st.title("🛡️ DevSecOps Omni-Architect")
    st.info("Please use the 'Open File Browser' in the sidebar to choose files.")
else:
    st.title(f"🚀 Project: {', '.join(st.session_state.selected_apps)}")
    target_env = st.selectbox("Target Provider:", list(CLOUD_CONFIG.keys()))
    tabs = st.tabs(["🐳 Infra", "🌍 IaC (Terraform)", "🔭 Observability", "🛡️ Compliance", "📖 Docs"])

    # Reusable function to parse AI output and show Download Buttons
    def render_manifests(raw_text):
        if "---FILE:" not in raw_text:
            st.warning("The AI output format was unexpected. Showing raw text instead.")
            st.text_area("Full Output", raw_text, height=400)
            return

        parts = raw_text.split("---FILE:")[1:]
        for part in parts:
            try:
                header_and_code = part.strip().split("\n", 1)
                filename = header_and_code[0].replace("---", "").strip()
                code_content = header_and_code[1].strip()
                
                with st.container(border=True):
                    col_tit, col_dl = st.columns([0.8, 0.2])
                    col_tit.subheader(f"📄 {filename}")
                    col_dl.download_button("📥 Download", data=code_content, file_name=filename, key=f"dl_{filename}_{os.urandom(4).hex()}")
                    st.code(code_content, language="yaml" if any(x in filename for x in [".yaml", ".yml", ".tf"]) else "dockerfile")
            except: continue

    with tabs[0]: # INFRA
        itype = st.radio("Output:", ["Simple Dockerfile", "Docker Compose", "Kubernetes Manifests"], horizontal=True)
        if st.button(f"Generate {itype}", type="primary"):
            prompt = f"Act as SRE. Generate {itype} for {st.session_state.selected_apps} targeting {target_env}. Every file must start with '---FILE: filename---' marker."
            st.session_state['infra_res'] = ask_ollama(selected_model, prompt)
        if 'infra_res' in st.session_state: render_manifests(st.session_state['infra_res'])

    with tabs[1]: # IaC (Terraform)
        if st.button("🏗️ Build Terraform"):
            prompt = f"Generate Terraform (main.tf, variables.tf, outputs.tf) for {target_env}. Every file must start with '---FILE: filename---' marker."
            st.session_state['tf_res'] = ask_ollama(selected_model, prompt)
        if 'tf_res' in st.session_state: render_manifests(st.session_state['tf_res'])

    with tabs[2]: # Observability
        strategy = st.radio("Mode:", ["Universal Sidecar", "SDK Implementation"], horizontal=True)
        if st.button("🚀 Architect OTel"):
            prompt = f"Generate {strategy} configuration for {st.session_state.selected_apps}. If sidecar, provide K8s YAML and ConfigMap starting with '---FILE: filename---'."
            st.session_state['otel_res'] = ask_ollama(selected_model, prompt)
        if 'otel_res' in st.session_state: render_manifests(st.session_state['otel_res'])

    with tabs[3]: # Compliance
        std = st.selectbox("Standard:", ["CIS Benchmark", "SOC2 Readiness", "Standard SRE Audit"])
        if st.button("🔍 Run Audit"):
            ctx = st.session_state.get('infra_res', '') + st.session_state.get('tf_res', '')
            st.markdown(ask_ollama(selected_model, f"Audit these configs against {std}: \n{ctx}"))

    with tabs[4]: # Docs
        if st.button("📝 Create README"):
            st.markdown(ask_ollama(selected_model, f"Create a production README for {st.session_state.selected_apps}."))