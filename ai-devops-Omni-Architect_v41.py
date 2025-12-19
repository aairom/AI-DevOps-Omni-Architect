# ai-devops-Omni-Architect_v41.py
import streamlit as st
import ollama
import os, subprocess, uuid, requests
from pathlib import Path
from dotenv import load_dotenv

# --- 1. IMMUTABLE CONFIGURATION ---
load_dotenv()
K8S_FLAVORS = ["Standard (Vanilla)", "Minikube (Local VM)", "Kind (Docker-in-Docker)", "Google (GKE)", "AWS (EKS)", "Azure (AKS)", "IBM (IKS)"]
TF_PROVIDERS = ["AWS", "GCP", "IBM Cloud", "Azure", "Oracle Cloud"]
APP_EXTS = {'.c', '.cpp', '.go', '.php', '.js', '.ts', '.java', '.html', '.sh'}

# --- 2. PERSISTENT STATE ---
if 'state' not in st.session_state:
    st.session_state.state = {
        'current_dir': os.getcwd(),
        'selected_files': [],
        'ai_prov': "Local (Ollama)",
        'ai_model': "",
        'keys': {
            'gemini': os.getenv("GEMINI_API_KEY", ""),
            'watsonx_api': os.getenv("WATSONX_API_KEY", ""),
            'watsonx_project': os.getenv("WATSONX_PROJECT_ID", "")
        },
        'infra_out': "",
        'obs_out': "",
        'gen_cache': {}
    }

st.set_page_config(page_title="Omni-Architect v41.1", layout="wide", page_icon="🛡️")

# --- 3. CORE LOGIC (AI & DISCOVERY) ---
@st.cache_data(ttl=10)
def discover_ollama():
    try:
        return [m.model for m in ollama.list().models]
    except:
        try:
            res = requests.get("http://localhost:11434/api/tags", timeout=1)
            return [m['name'] for m in res.json().get('models', [])] if res.status_code == 200 else []
        except: return []

def get_watsonx_token(api_key):
    url = "https://iam.cloud.ibm.com/identity/token"
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
    try:
        res = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
        return res.json().get("access_token")
    except: return None

def ask_ai(prompt):
    prov, model, keys = st.session_state.state['ai_prov'], st.session_state.state['ai_model'], st.session_state.state['keys']
    try:
        with st.spinner(f"🤖 {prov} is architecting..."):
            if prov == "Local (Ollama)":
                return ollama.generate(model=model, prompt=prompt)['response']
            
            elif prov == "Google (Gemini)":
                import google.generativeai as genai
                genai.configure(api_key=keys['gemini'])
                return genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
            
            elif prov == "IBM watsonx":
                token = get_watsonx_token(keys['watsonx_api'])
                url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                body = {
                    "input": f"<s>[INST] {prompt} [/INST]",
                    "parameters": {"max_new_tokens": 1200},
                    "project_id": keys['watsonx_project']
                }
                return requests.post(url, headers=headers, json=body).json()['results'][0]['generated_text']
    except Exception as e: return f"Error: {e}"

def render_registry(text):
    """Universal renderer for AI file blocks with download buttons"""
    if not text or "---FILE:" not in text:
        st.markdown(text); return
    
    for part in text.split("---FILE:")[1:]:
        try:
            fname, content = part.strip().split("\n", 1)
            fname, content = fname.strip(), content.strip()
            st.session_state.state['gen_cache'][fname] = content
            
            with st.container(border=True):
                h_col, b_col = st.columns([0.8, 0.2])
                h_col.subheader(f"📄 {fname}")
                b_col.download_button("📥 Download", content, file_name=fname, key=f"dl_{fname}_{uuid.uuid4().hex}")
                st.code(content, language="hcl" if ".tf" in fname else "yaml")
        except: continue

# --- 4. SIDEBAR (GUI NAVIGATION) ---
with st.sidebar:
    st.header("⚙️ Controller")
    st.session_state.state['ai_prov'] = st.selectbox("LLM Provider:", ["Local (Ollama)", "IBM watsonx", "Google (Gemini)"])
    
    if st.session_state.state['ai_prov'] == "Local (Ollama)":
        models = discover_ollama()
        st.session_state.state['ai_model'] = st.selectbox("Local Model:", models) if models else st.text_input("Model Name (Manual):")
    elif st.session_state.state['ai_prov'] == "Google (Gemini)":
        st.session_state.state['keys']['gemini'] = st.text_input("Gemini Key:", type="password", value=st.session_state.state['keys']['gemini'])
    elif st.session_state.state['ai_prov'] == "IBM watsonx":
        st.session_state.state['keys']['watsonx_api'] = st.text_input("IAM Key:", type="password", value=st.session_state.state['keys']['watsonx_api'])
        st.session_state.state['keys']['watsonx_project'] = st.text_input("Project ID:", value=st.session_state.state['keys']['watsonx_project'])

    st.divider()
    st.subheader("📂 File Explorer")
    c1, c2 = st.columns(2)
    if c1.button("⬅️ Up"): 
        st.session_state.state['current_dir'] = os.path.dirname(st.session_state.state['current_dir']); st.rerun()
    if c2.button("🏠 Home"): 
        st.session_state.state['current_dir'] = os.getcwd(); st.rerun()

    try:
        items = os.listdir(st.session_state.state['current_dir'])
        folders = sorted([f for f in items if os.path.isdir(os.path.join(st.session_state.state['current_dir'], f))])
        files = sorted([f for f in items if os.path.isfile(os.path.join(st.session_state.state['current_dir'], f))])
        
        target = st.selectbox("Go to Folder:", ["."] + folders)
        if target != ".":
            st.session_state.state['current_dir'] = os.path.join(st.session_state.state['current_dir'], target); st.rerun()

        st.divider()
        use_filter = st.toggle("✨ Smart Filter (App Code)", value=False)
        suggested = [f for f in files if Path(f).suffix.lower() in APP_EXTS]
        st.session_state.state['selected_files'] = st.multiselect("📑 Select Files:", options=files, default=suggested if use_filter else [])
    except Exception as e: st.error(f"IO Error: {e}")

# --- 5. MAIN UI ---
st.title("🛡️ Omni-Architect v41.1")

if not st.session_state.state['selected_files']:
    st.info("👈 Use the Explorer to select your project files.")
else:
    tabs = st.tabs(["🏗️ Infra & IaC", "🔭 Observability", "🛡️ Security", "🚀 Execution"])

    with tabs[0]: # INFRA
        col1, col2 = st.columns(2)
        strategy = col1.selectbox("Strategy:", ["Dockerfile", "Docker Compose", "Kubernetes Manifests", "Terraform (IaC)"])
        flavor = col2.selectbox("Target Flavor:", K8S_FLAVORS if strategy == "Kubernetes Manifests" else (TF_PROVIDERS if strategy == "Terraform (IaC)" else ["N/A"]))

        if st.button(f"Generate {strategy}", type="primary", use_container_width=True):
            paths = [os.path.join(st.session_state.state['current_dir'], f) for f in st.session_state.state['selected_files']]
            st.session_state.state['infra_out'] = ask_ai(f"Write {strategy} for {paths} on {flavor}. Use ---FILE: filename---")
        render_registry(st.session_state.state['infra_out'])

    with tabs[1]: # OBSERVABILITY RESTORED
        st.subheader("🔭 OpenTelemetry Strategy")
        
        obs_mode = st.radio("Choose OTel Pattern:", 
                            ["Universal Sidecar (K8s/Infra)", "SDK Implementation (Code-level)"], 
                            horizontal=True)
        
        c1, c2 = st.columns(2)
        
        if c1.button("🧪 Apply Telemetry", type="primary", use_container_width=True):
            if obs_mode == "Universal Sidecar (K8s/Infra)":
                if not st.session_state.state['infra_out']:
                    st.error("❌ No Infrastructure found! Please generate K8s Manifests in the 'Infra' tab first.")
                else:
                    prompt = f"Inject an OpenTelemetry Collector sidecar into these K8s manifests: {st.session_state.state['infra_out']}. Use ---FILE: filename---"
                    st.session_state.state['infra_out'] = ask_ai(prompt)
                    st.rerun()
            else:
                prompt = f"Analyze these files: {st.session_state.state['selected_files']}. Rewrite them to implement OTel SDK. Use ---FILE: filename---"
                st.session_state.state['obs_out'] = ask_ai(prompt)
                st.rerun()

        if c2.button("📊 Gen Grafana/Prometheus", use_container_width=True):
            st.session_state.state['obs_out'] = ask_ai(f"Generate Prometheus rules and Grafana dashboard for: {st.session_state.state['selected_files']}")
            st.rerun()

        render_registry(st.session_state.state['obs_out'])

    with tabs[2]: # SECURITY
        s1, s2 = st.columns(2)
        if s1.button("🛡️ Harden Security", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"Apply DevSecOps hardening (non-root, read-only fs, etc) to: {st.session_state.state['infra_out']}")
            st.rerun()
        if s2.button("💰 FinOps Optimize", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"Optimize CPU/Memory requests and cloud costs for: {st.session_state.state['infra_out']}")
            st.rerun()

    with tabs[3]: # EXECUTION
        cmd = st.text_input("Terminal:", value="ls -la")
        if st.button("🚀 Commit & Run Command", type="primary"):
            for f, c in st.session_state.state['gen_cache'].items():
                with open(os.path.join(st.session_state.state['current_dir'], f), 'w') as file: file.write(c)
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=st.session_state.state['current_dir'])
            st.text_area("Output:", res.stdout if res.returncode == 0 else res.stderr)