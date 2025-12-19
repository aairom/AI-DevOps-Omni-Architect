import streamlit as st
import ollama
import os
import subprocess
import uuid
import requests
from pathlib import Path
from dotenv import load_dotenv

# --- 1. CONFIG & STATE ---
load_dotenv()
# The defined Helper Filter Extensions
APP_EXTS = {'.c', '.cpp', '.go', '.php', '.js', '.ts', '.java', '.html', '.sh'}

if 'state' not in st.session_state:
    st.session_state.state = {
        'current_dir': os.getcwd(),
        'selected_files': [],
        'ai_prov': "Local (Ollama)",
        'ai_model': "llama3.2",
        'keys': {
            'gemini': os.getenv("GEMINI_API_KEY", ""),
            'openai': os.getenv("OPENAI_API_KEY", ""),
            'watsonx_api': os.getenv("WATSONX_API_KEY", ""),
            'watsonx_project': os.getenv("WATSONX_PROJECT_ID", "")
        },
        'infra_out': "",
        'gen_cache': {} 
    }

st.set_page_config(page_title="Omni-Architect v36.0", layout="wide", page_icon="🛡️")

# --- 2. AI UTILITIES ---
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
        with st.spinner(f"🤖 Architecting via {prov}..."):
            if prov == "Local (Ollama)":
                return ollama.generate(model=model, prompt=prompt)['response']
            elif prov == "Google (Gemini)":
                import google.generativeai as genai
                genai.configure(api_key=keys['gemini'])
                return genai.GenerativeModel(model).generate_content(prompt).text
            elif prov == "IBM watsonx":
                token = get_watsonx_token(keys['watsonx_api'])
                url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                body = {"input": f"<s>[INST] {prompt} [/INST]", "parameters": {"max_new_tokens": 1200}, "project_id": keys['watsonx_project']}
                return requests.post(url, headers=headers, json=body).json()['results'][0]['generated_text']
    except Exception as e: return f"Error: {e}"

def render_registry(text):
    if not text or "---FILE:" not in text: 
        st.markdown(text); return
    for p in text.split("---FILE:")[1:]:
        try:
            fname, content = p.strip().split("\n", 1)
            fname, content = fname.strip(), content.strip()
            st.session_state.state['gen_cache'][fname] = content
            with st.container(border=True):
                c1, c2 = st.columns([0.8, 0.2])
                c1.subheader(f"📄 {fname}")
                c2.download_button("📥 Download", content, file_name=fname, key=f"dl_{fname}_{uuid.uuid4().hex}")
                st.code(content, language="hcl" if ".tf" in fname else "yaml")
        except: continue

# --- 3. SIDEBAR: VISUAL EXPLORER & SMART FILTER ---
with st.sidebar:
    st.header("⚙️ Global Control")
    st.session_state.state['ai_prov'] = st.selectbox("LLM Provider:", ["Local (Ollama)", "IBM watsonx", "Google (Gemini)", "OpenAI"])
    
    st.divider()
    st.subheader("📂 Visual Explorer")
    
    # Navigation
    c_up, c_home = st.columns(2)
    if c_up.button("⬅️ Up"): st.session_state.state['current_dir'] = os.path.dirname(st.session_state.state['current_dir']); st.rerun()
    if c_home.button("🏠 Home"): st.session_state.state['current_dir'] = os.getcwd(); st.rerun()

    # Get Directory Content
    try:
        items = os.listdir(st.session_state.state['current_dir'])
        folders = sorted([f for f in items if os.path.isdir(os.path.join(st.session_state.state['current_dir'], f))])
        all_files = sorted([f for f in items if os.path.isfile(os.path.join(st.session_state.state['current_dir'], f))])
        
        # Folder Navigation
        sel_folder = st.selectbox("Go to Folder:", ["."] + folders)
        if sel_folder != ".":
            st.session_state.state['current_dir'] = os.path.join(st.session_state.state['current_dir'], sel_folder)
            st.rerun()

        st.divider()
        
        # --- SMART FILTER LOGIC ---
        # 1. Identify which files match the "App Code" criteria
        app_code_files = [f for f in all_files if Path(f).suffix.lower() in APP_EXTS]
        
        use_filter = st.toggle("✨ Smart Auto-Select App Code", value=False)
        
        # 2. Determine default selection
        default_selection = app_code_files if use_filter else []

        # 3. Multiselect displays ALL files, but default is set by the filter
        st.session_state.state['selected_files'] = st.multiselect(
            "📑 Select Files:", 
            options=all_files, 
            default=default_selection,
            help="Toggle the switch above to automatically highlight C, Go, JS, etc."
        )

    except Exception as e:
        st.error(f"Access Error: {e}")

# --- 4. MAIN DASHBOARD ---
st.title("🛡️ DevSecOps Omni-Architect v36.0")

if not st.session_state.state['selected_files']:
    st.info("👈 Use the Explorer to navigate and select files. Use 'Smart Auto-Select' to highlight code automatically.")
else:
    tabs = st.tabs(["🏗️ Infra & IaC", "🔭 Observability", "🛡️ Security", "🚀 Execution"])

    with tabs[0]: # INFRA
        m_col, f_col = st.columns(2)
        mode = m_col.selectbox("Strategy:", ["Single Dockerfile", "Docker Compose", "Kubernetes Manifests", "Terraform (IaC)"])
        flavor = f_col.selectbox("Target Environment:", ["GKE", "EKS", "AKS", "IBM Cloud", "On-Premise"])
        
        if st.button(f"Generate {mode}", type="primary", use_container_width=True):
            full_paths = [os.path.join(st.session_state.state['current_dir'], f) for f in st.session_state.state['selected_files']]
            st.session_state.state['infra_out'] = ask_ai(f"Architect {mode} for: {full_paths}. Environment: {flavor}. Use ---FILE: filename---")
        render_registry(st.session_state.state['infra_out'])

    with tabs[3]: # EXECUTION
        cmd = st.text_input("Run Command:", "ls -la")
        if st.button("🚀 Write & Execute", type="primary"):
            for f, c in st.session_state.state['gen_cache'].items():
                with open(os.path.join(st.session_state.state['current_dir'], f), 'w') as file: file.write(c)
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=st.session_state.state['current_dir'])
            st.code(res.stdout if res.returncode == 0 else res.stderr)