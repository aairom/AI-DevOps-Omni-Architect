import streamlit as st
import ollama
import os
import subprocess
import json
import uuid
import requests
from pathlib import Path
from dotenv import load_dotenv

# --- 1. PERSISTENT STATE VAULT ---
load_dotenv()
if 'state' not in st.session_state:
    st.session_state.state = {
        'files': [],
        'path': os.getcwd(),
        'ai_prov': "Local (Ollama)",
        'ai_model': "llama3.2",
        'keys': {
            'gemini': os.getenv("GEMINI_API_KEY", ""),
            'openai': os.getenv("OPENAI_API_KEY", ""),
            'watsonx_api': os.getenv("WATSONX_API_KEY", ""),
            'watsonx_project': os.getenv("WATSONX_PROJECT_ID", "")
        },
        'infra_out': "",
        'obs_out': "",
        'pipe_out': "",
        'policy_out': "",
        'gen_cache': {} 
    }

st.set_page_config(page_title="Omni-Architect v29.0", layout="wide", page_icon="🛡️")

# --- 2. AI CORE ENGINE (Enterprise Multi-Model) ---
def get_watsonx_token(api_key):
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

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
                res = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
                return res.choices[0].message.content
            elif prov == "IBM WatsonX":
                token = get_watsonx_token(keys['watsonx_api'])
                url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                body = {"input": f"<s>[INST] {prompt} [/INST]", "parameters": {"max_new_tokens": 1000}, "project_id": keys['watsonx_project']}
                return requests.post(url, headers=headers, json=body).json()['results'][0]['generated_text']
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
                st.code(content, language="yaml" if any(x in fname for x in [".yaml", ".yml", ".tf", ".rego"]) else "dockerfile")
        except: continue

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Global Control")
    st.session_state.state['ai_prov'] = st.selectbox("LLM Provider:", ["Local (Ollama)", "Google (Gemini)", "OpenAI", "IBM WatsonX"])
    
    if st.session_state.state['ai_prov'] == "Google (Gemini)":
        st.session_state.state['keys']['gemini'] = st.text_input("Gemini Key:", type="password", value=st.session_state.state['keys']['gemini'])
        st.session_state.state['ai_model'] = "gemini-1.5-flash"
    elif st.session_state.state['ai_prov'] == "OpenAI":
        st.session_state.state['keys']['openai'] = st.text_input("OpenAI Key:", type="password", value=st.session_state.state['keys']['openai'])
        st.session_state.state['ai_model'] = "gpt-4o"
    elif st.session_state.state['ai_prov'] == "IBM WatsonX":
        st.session_state.state['keys']['watsonx_api'] = st.text_input("IBM API Key:", type="password", value=st.session_state.state['keys']['watsonx_api'])
        st.session_state.state['keys']['watsonx_project'] = st.text_input("Project ID:", value=st.session_state.state['keys']['watsonx_project'])
        st.session_state.state['ai_model'] = "ibm/granite-13b-instruct-v2"
    else:
        try: m_list = [m.model for m in ollama.list().models]; st.session_state.state['ai_model'] = st.selectbox("Local Model:", m_list)
        except: st.session_state.state['ai_model'] = st.text_input("Model:", "llama3.2")

    st.divider()
    if st.button("📁 Refresh Directory"):
        st.session_state.state['files'] = [f for f in os.listdir(st.session_state.state['path']) if not f.startswith('.')]
    active_files = st.multiselect("Active Context:", st.session_state.state['files'], default=st.session_state.state['files'][:1])

# --- 4. MAIN DASHBOARD ---
st.title("🛡️ DevSecOps Omni-Architect v29.0")

if not active_files:
    st.info("👈 Select files in the sidebar to begin.")
else:
    tabs = st.tabs(["🏗️ Infra", "🔭 Observability", "⚖️ Governance (OPA)", "⛓️ Pipelines", "🚀 Execution"])

    with tabs[0]: # INFRA
        c1, c2 = st.columns(2)
        mode = c1.selectbox("Strategy:", ["Single Dockerfile", "Docker Compose", "Kubernetes Manifests"])
        flavor = c2.selectbox("K8s Flavor:", ["Standard", "Minikube", "Kind", "GKE", "IKS", "EKS", "AKS"]) if mode == "Kubernetes Manifests" else "N/A"
        if st.button(f"Generate {mode}", type="primary", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"Generate {mode} for {active_files}. Flavor: {flavor}. Use ---FILE: filename---")
        render_registry(st.session_state.state['infra_out'])

    with tabs[1]: # OBSERVABILITY
        o1, o2 = st.columns(2)
        if o1.button("Inject OTel Sidecar", use_container_width=True):
            st.session_state.state['infra_out'] = ask_ai(f"Add OTel sidecar to: {st.session_state.state['infra_out']}. Use ---FILE: k8s-otel.yaml---")
            st.rerun()
        if o2.button("OTel + Grafana + Prometheus", use_container_width=True):
            st.session_state.state['obs_out'] = ask_ai(f"Generate OTel, Grafana JSON, and Prometheus alerts for {active_files}.")
        render_registry(st.session_state.state['obs_out'])

    with tabs[2]: # GOVERNANCE (OPA)
        st.subheader("Policy-as-Code (Gatekeeper)")
        p_goal = st.selectbox("Policy Goal:", ["Disallow Root Containers", "Require Resource Limits", "Enforce Image Purity", "Restrict LoadBalancers"])
        if st.button("Generate OPA Rego Policy", type="primary", use_container_width=True):
            prompt = f"Create an OPA Gatekeeper ConstraintTemplate and Constraint for: {p_goal}. Target: Kubernetes. Use ---FILE: policy.rego---"
            st.session_state.state['policy_out'] = ask_ai(prompt)
        render_registry(st.session_state.state['policy_out'])

    with tabs[3]: # PIPELINES
        p_type = st.selectbox("Pipeline Type:", ["GitHub Actions", "GitLab CI", "Jenkins Pipeline"])
        if st.button(f"Generate {p_type} Workflow", use_container_width=True):
            st.session_state.state['pipe_out'] = ask_ai(f"Create a {p_type} pipeline for {active_files} including Trivy scans. Use ---FILE: pipeline.yaml---")
        render_registry(st.session_state.state['pipe_out'])

    with tabs[4]: # EXECUTION
        cmd = st.text_input("Bash Command:", "kubectl apply -f .")
        if st.button("🚀 Commit & Execute", type="primary"):
            for f, c in st.session_state.state['gen_cache'].items():
                with open(os.path.join(st.session_state.state['path'], f), 'w') as file: file.write(c)
            subprocess.run("git init && git add . && git commit -m 'ops update'", shell=True, cwd=st.session_state.state['path'])
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=st.session_state.state['path'])
            st.code(res.stdout if res.returncode == 0 else res.stderr)