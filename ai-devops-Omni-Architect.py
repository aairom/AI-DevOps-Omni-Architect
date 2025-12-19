import streamlit as st
import ollama
import os
import subprocess
import json
import uuid
import requests
from pathlib import Path
from dotenv import load_dotenv

# --- 1. PERSISTENT STATE VAULT (Multi-Key Support) ---
load_dotenv()

if 'state' not in st.session_state:
    st.session_state.state = {
        'files': [],
        'path': os.getcwd(),
        'ai_prov': "Local (Ollama)",
        'ai_model': "llama3.2",
        # Auto-load all enterprise keys
        'keys': {
            'gemini': os.getenv("GEMINI_API_KEY", ""),
            'openai': os.getenv("OPENAI_API_KEY", ""),
            'watsonx_api': os.getenv("WATSONX_API_KEY", ""),
            'watsonx_project': os.getenv("WATSONX_PROJECT_ID", "")
        },
        'infra_out': "",
        'obs_out': "",
        'gen_cache': {} 
    }

st.set_page_config(page_title="Omni-Architect v26.0", layout="wide", page_icon="🏗️")

# --- 2. MULTI-PROVIDER AI ENGINE ---
def ask_ai(prompt):
    prov = st.session_state.state['ai_prov']
    model = st.session_state.state['ai_model']
    keys = st.session_state.state['keys']
    
    try:
        with st.spinner(f"🤖 {prov} is architecting..."):
            if prov == "Local (Ollama)":
                return ollama.generate(model=model, prompt=prompt)['response']
            
            elif prov == "Google (Gemini)":
                import google.generativeai as genai
                genai.configure(api_key=keys['gemini'])
                return genai.GenerativeModel(model).generate_content(prompt).text
            
            elif prov == "OpenAI":
                from openai import OpenAI
                client = OpenAI(api_key=keys['openai'])
                res = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return res.choices[0].message.content
            
            elif prov == "IBM WatsonX":
                # Implementation via direct REST to avoid heavy library dependencies
                url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {keys['watsonx_api']}" # Simplified for example
                }
                body = {
                    "input": prompt,
                    "parameters": {"max_new_tokens": 1000},
                    "project_id": keys['watsonx_project']
                }
                # Note: WatsonX usually requires an IAM token exchange first
                return "WatsonX Response (Connect via IAM token)" 
                
    except Exception as e: return f"Error: {e}"

def render_registry(text):
    if not text or "---FILE:" not in text: 
        st.markdown(text); return
    parts = text.split("---FILE:")[1:]
    for p in parts:
        try:
            fname, body = p.strip().split("\n", 1)
            fname = fname.strip(); content = body.strip()
            st.session_state.state['gen_cache'][fname] = content
            with st.container(border=True):
                col_t, col_b = st.columns([0.8, 0.2])
                col_t.subheader(f"📄 {fname}")
                col_b.download_button("📥 Download", content, file_name=fname, key=f"dl_{fname}_{uuid.uuid4().hex}")
                st.code(content, language="yaml" if any(x in fname for x in [".yaml", ".tf"]) else "dockerfile")
        except: continue

# --- 3. SIDEBAR (STABLE CONFIG & KEY MANAGEMENT) ---
with st.sidebar:
    st.header("⚙️ Global Brain")
    st.session_state.state['ai_prov'] = st.selectbox("LLM Provider:", 
        ["Local (Ollama)", "IBM watsonx", "Google (Gemini)", "OpenAI"])
    
    # Dynamic Key Inputs based on Provider
    if st.session_state.state['ai_prov'] == "Google (Gemini)":
        st.session_state.state['keys']['gemini'] = st.text_input("Gemini Key:", type="password", value=st.session_state.state['keys']['gemini'])
        st.session_state.state['ai_model'] = "gemini-1.5-flash"
    elif st.session_state.state['ai_prov'] == "OpenAI":
        st.session_state.state['keys']['openai'] = st.text_input("OpenAI Key:", type="password", value=st.session_state.state['keys']['openai'])
        st.session_state.state['ai_model'] = "gpt-4o"
    elif st.session_state.state['ai_prov'] == "IBM watsonx":
        st.session_state.state['keys']['watsonx_api'] = st.text_input("IAM API Key:", type="password", value=st.session_state.state['keys']['watsonx_api'])
        st.session_state.state['keys']['watsonx_project'] = st.text_input("Project ID:", value=st.session_state.state['keys']['watsonx_project'])
        st.session_state.state['ai_model'] = "ibm/granite-13b-instruct-v2"
    else:
        try:
            m_list = [m.model for m in ollama.list().models]
            st.session_state.state['ai_model'] = st.selectbox("Local Model:", m_list)
        except: st.session_state.state['ai_model'] = st.text_input("Model:", "llama3.2")

    st.divider()
    if st.button("📁 Refresh Project Directory"):
        st.session_state.state['files'] = [f for f in os.listdir(st.session_state.state['path']) if not f.startswith('.')]
    
    active_files = st.multiselect("Context:", st.session_state.state['files'], default=st.session_state.state['files'][:1])

# --- 4. MAIN DASHBOARD ---
st.title("🛡️ DevSecOps Omni-Architect v26.0")

if not active_files:
    st.info("👈 Select files in the sidebar.")
else:
    tabs = st.tabs(["🏗️ Infra (Docker/K8s)", "🔭 Observability", "🛡️ Security & FinOps", "🚀 Execution"])

    with tabs[0]:
        st.subheader("Compute & Orchestration")
        c1, c2 = st.columns(2)
        mode = c1.selectbox("Strategy:", ["Single Dockerfile", "Docker Compose", "Kubernetes Manifests"])
        flavor = c2.selectbox("K8s Flavor:", ["Standard", "Minikube", "Kind", "GKE", "IKS", "EKS", "AKS"]) if mode == "Kubernetes Manifests" else "N/A"
        
        if st.button(f"Generate {mode}", type="primary", use_container_width=True):
            p = f"Create {mode} for {active_files}. Flavor: {flavor}. Use ---FILE: filename--- markers."
            st.session_state.state['infra_out'] = ask_ai(p)
        render_registry(st.session_state.state['infra_out'])

    with tabs[1]:
        st.subheader("OTel, Grafana & Sidecars")
        o1, o2, o3 = st.columns(3)
        if o1.button("Inject OTel Sidecar", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"Add OTel sidecar to: {st.session_state.state['infra_out']}")
            st.rerun()
        if o2.button("Generate OTel Config", use_container_width=True):
            st.session_state.state['obs_out'] = ask_ai(f"Generate otel-collector.yaml for {active_files}.")
        if o3.button("Grafana + Prometheus", use_container_width=True):
            st.session_state.state['obs_out'] = ask_ai(f"Generate Grafana JSON and Prometheus rules for {active_files}.")
        render_registry(st.session_state.state['obs_out'])

    with tabs[2]:
        s1, s2 = st.columns(2)
        if s1.button("Harden Infrastructure", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"Secure this: {st.session_state.state['infra_out']}")
            st.rerun()
        if s2.button("Optimize Costs", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"FinOps optimize: {st.session_state.state['infra_out']}")
            st.rerun()

    with tabs[3]:
        st.subheader("Live Deployment")
        cmd = st.text_input("CLI:", "kubectl apply -f .")
        if st.button("🚀 Commit & Execute", type="primary"):
            for f, c in st.session_state.state['gen_cache'].items():
                with open(os.path.join(st.session_state.state['path'], f), 'w') as file: file.write(c)
            subprocess.run("git init && git add . && git commit -m 'ops update'", shell=True, cwd=st.session_state.state['path'])
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=st.session_state.state['path'])
            st.code(res.stdout if res.returncode == 0 else res.stderr)