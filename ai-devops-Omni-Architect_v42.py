"""
AI-DevOps Omni-Architect v42.0
Enhanced version with modular architecture, security improvements, and extended features
"""
import streamlit as st
import os
import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Import custom modules
from config import Config, logger
from utils import security_manager, cache_manager, GitManager
from providers import AIProviderFactory

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title=f"{Config.APP_NAME} {Config.APP_VERSION}",
    layout="wide",
    page_icon=Config.APP_ICON
)

# --- SESSION STATE INITIALIZATION ---
if 'state' not in st.session_state:
    st.session_state.state = {
        'current_dir': str(Config.BASE_DIR),
        'selected_files': [],
        'ai_prov': "Local (Ollama)",
        'ai_model': "",
        'keys': {
            'gemini': Config.GEMINI_API_KEY,
            'watsonx_api': Config.WATSONX_API_KEY,
            'watsonx_project': Config.WATSONX_PROJECT_ID,
            'openai': Config.OPENAI_API_KEY
        },
        'infra_out': "",
        'obs_out': "",
        'gen_cache': {},
        'git_manager': None,
        'max_tokens': Config.DEFAULT_MAX_TOKENS,
        'temperature': Config.DEFAULT_TEMPERATURE
    }

# --- CORE FUNCTIONS ---
@st.cache_data(ttl=10)
def discover_ollama() -> List[str]:
    """Discover available Ollama models"""
    try:
        import ollama
        return [m.model for m in ollama.list().models if m.model]
    except:
        try:
            import requests
            res = requests.get("http://localhost:11434/api/tags", timeout=1)
            return [m['name'] for m in res.json().get('models', [])] if res.status_code == 200 else []
        except:
            return []

def ask_ai(prompt: str, use_cache: bool = True) -> str:
    """
    Generate AI response with caching and error handling
    """
    prov = st.session_state.state['ai_prov']
    model = st.session_state.state['ai_model']
    keys = st.session_state.state['keys']
    
    # Check cache first
    if use_cache:
        cached = cache_manager.get(prompt, prov, model)
        if cached:
            logger.info(f"Using cached response for {prov}")
            return cached
    
    try:
        with st.spinner(f"🤖 {prov} is architecting..."):
            # Prepare provider config
            config = {}
            if prov == "Google (Gemini)":
                config['api_key'] = keys['gemini']
            elif prov == "IBM watsonx":
                config['api_key'] = keys['watsonx_api']
                config['project_id'] = keys['watsonx_project']
            elif prov == "OpenAI (GPT-4)":
                config['api_key'] = keys['openai']
            
            # Create provider and generate
            provider = AIProviderFactory.create_provider(prov, model, config)
            
            # Validate configuration
            if not provider.validate_config():
                return "❌ Error: Invalid provider configuration. Please check your API keys."
            
            # Generate response
            response = provider.generate(
                prompt,
                max_tokens=st.session_state.state['max_tokens'],
                temperature=st.session_state.state['temperature']
            )
            
            # Cache the response
            if use_cache:
                cache_manager.set(prompt, prov, model, response)
            
            logger.info(f"Generated response using {prov}")
            return response
            
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logger.error(f"AI generation failed: {e}")
        return error_msg

def render_registry(text: str):
    """Universal renderer for AI file blocks with download buttons"""
    if not text or "---FILE:" not in text:
        st.markdown(text)
        return
    
    for part in text.split("---FILE:")[1:]:
        try:
            fname, content = part.strip().split("\n", 1)
            fname = fname.strip()
            content = content.strip()
            
            # Sanitize filename
            fname = security_manager.sanitize_filename(fname)
            st.session_state.state['gen_cache'][fname] = content
            
            with st.container(border=True):
                h_col, b_col = st.columns([0.8, 0.2])
                h_col.subheader(f"📄 {fname}")
                b_col.download_button(
                    "📥 Download",
                    content,
                    file_name=fname,
                    key=f"dl_{fname}_{uuid.uuid4().hex}"
                )
                
                # Determine language for syntax highlighting
                lang = "yaml"
                if ".tf" in fname:
                    lang = "hcl"
                elif ".py" in fname:
                    lang = "python"
                elif ".js" in fname or ".ts" in fname:
                    lang = "javascript"
                elif ".sh" in fname:
                    lang = "bash"
                
                st.code(content, language=lang)
        except Exception as e:
            logger.error(f"Error rendering file block: {e}")
            continue

def safe_execute_command(command: str, cwd: str) -> tuple[bool, str]:
    """
    Safely execute command with validation
    Returns: (success, output)
    """
    # Validate command
    is_valid, result = security_manager.sanitize_command(command, Config.ALLOWED_COMMANDS)
    if not is_valid:
        logger.warning(f"Command rejected: {command}")
        return False, f"❌ Security Error: {result}"
    
    # Validate working directory
    is_valid, validated_path = security_manager.validate_file_path(cwd, str(Config.BASE_DIR))
    if not is_valid:
        return False, f"❌ Invalid directory: {validated_path}"
    
    try:
        # Execute command safely (without shell=True)
        import shlex
        cmd_parts = shlex.split(command)
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            cwd=validated_path,
            timeout=30
        )
        
        output = result.stdout if result.returncode == 0 else result.stderr
        logger.info(f"Command executed: {command}")
        return result.returncode == 0, output
        
    except subprocess.TimeoutExpired:
        return False, "❌ Command timeout (30s limit)"
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return False, f"❌ Error: {str(e)}"

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("⚙️ Controller")
    
    # AI Provider Selection
    st.session_state.state['ai_prov'] = st.selectbox(
        "LLM Provider:",
        Config.AI_PROVIDERS
    )
    
    # Provider-specific configuration
    if st.session_state.state['ai_prov'] == "Local (Ollama)":
        models = discover_ollama()
        if models:
            st.session_state.state['ai_model'] = st.selectbox("Local Model:", models)
        else:
            st.session_state.state['ai_model'] = st.text_input("Model Name (Manual):")
    
    elif st.session_state.state['ai_prov'] == "Google (Gemini)":
        key_input = st.text_input(
            "Gemini Key:",
            type="password",
            value=st.session_state.state['keys']['gemini']
        )
        if key_input:
            st.session_state.state['keys']['gemini'] = key_input
    
    elif st.session_state.state['ai_prov'] == "IBM watsonx":
        api_key = st.text_input(
            "IAM Key:",
            type="password",
            value=st.session_state.state['keys']['watsonx_api']
        )
        project_id = st.text_input(
            "Project ID:",
            value=st.session_state.state['keys']['watsonx_project']
        )
        if api_key:
            st.session_state.state['keys']['watsonx_api'] = api_key
        if project_id:
            st.session_state.state['keys']['watsonx_project'] = project_id
    
    elif st.session_state.state['ai_prov'] == "OpenAI (GPT-4)":
        key_input = st.text_input(
            "OpenAI Key:",
            type="password",
            value=st.session_state.state['keys']['openai']
        )
        if key_input:
            st.session_state.state['keys']['openai'] = key_input
        st.session_state.state['ai_model'] = st.selectbox(
            "Model:",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        )
    
    # Advanced AI Parameters
    with st.expander("🎛️ Advanced Parameters"):
        st.session_state.state['max_tokens'] = st.slider(
            "Max Tokens:",
            500, 4000,
            st.session_state.state['max_tokens']
        )
        st.session_state.state['temperature'] = st.slider(
            "Temperature:",
            0.0, 1.0,
            st.session_state.state['temperature'],
            0.1
        )
    
    st.divider()
    
    # File Explorer
    st.subheader("📂 File Explorer")
    col1, col2 = st.columns(2)
    
    if col1.button("⬅️ Up"):
        st.session_state.state['current_dir'] = os.path.dirname(
            st.session_state.state['current_dir']
        )
        st.rerun()
    
    if col2.button("🏠 Home"):
        st.session_state.state['current_dir'] = str(Config.BASE_DIR)
        st.rerun()
    
    try:
        current_path = st.session_state.state['current_dir']
        items = os.listdir(current_path)
        folders = sorted([f for f in items if os.path.isdir(os.path.join(current_path, f))])
        files = sorted([f for f in items if os.path.isfile(os.path.join(current_path, f))])
        
        # Folder navigation
        target = st.selectbox("Go to Folder:", ["."] + folders)
        if target != ".":
            st.session_state.state['current_dir'] = os.path.join(current_path, target)
            st.rerun()
        
        st.divider()
        
        # Smart filter toggle
        use_filter = st.toggle("✨ Smart Filter (App Code)", value=False)
        suggested = [f for f in files if Path(f).suffix.lower() in Config.APP_EXTS]
        
        st.session_state.state['selected_files'] = st.multiselect(
            "📑 Select Files:",
            options=files,
            default=suggested if use_filter else []
        )
        
    except Exception as e:
        st.error(f"❌ IO Error: {e}")
        logger.error(f"File explorer error: {e}")
    
    st.divider()
    
    # Cache Management
    with st.expander("💾 Cache Management"):
        stats = cache_manager.get_stats()
        st.json(stats)
        if st.button("🗑️ Clear Cache"):
            cache_manager.clear()
            st.success("Cache cleared!")

# --- MAIN UI ---
st.title(f"{Config.APP_ICON} {Config.APP_NAME} {Config.APP_VERSION}")

# Configuration status
config_status = Config.validate_config()
if not all(config_status.values()):
    with st.expander("⚠️ Configuration Warnings", expanded=False):
        for key, status in config_status.items():
            if not status:
                st.warning(f"❌ {key.replace('_', ' ').title()}")

if not st.session_state.state['selected_files']:
    st.info("👈 Use the Explorer to select your project files.")
else:
    tabs = st.tabs([
        "🏗️ Infra & IaC",
        "🔭 Observability",
        "🛡️ Security",
        "🚀 Execution",
        "📊 Git Integration"
    ])
    
    # TAB 1: Infrastructure
    with tabs[0]:
        col1, col2 = st.columns(2)
        strategy = col1.selectbox(
            "Strategy:",
            ["Dockerfile", "Docker Compose", "Kubernetes Manifests", "Terraform (IaC)"]
        )
        
        if strategy == "Kubernetes Manifests":
            flavor = col2.selectbox("Target Flavor:", Config.K8S_FLAVORS)
        elif strategy == "Terraform (IaC)":
            flavor = col2.selectbox("Target Flavor:", Config.TF_PROVIDERS)
        else:
            flavor = "N/A"
        
        if st.button(f"Generate {strategy}", type="primary", use_container_width=True):
            paths = [
                os.path.join(st.session_state.state['current_dir'], f)
                for f in st.session_state.state['selected_files']
            ]
            prompt = f"Write {strategy} for {paths} on {flavor}. Use ---FILE: filename--- format for each file."
            st.session_state.state['infra_out'] = ask_ai(prompt)
        
        render_registry(st.session_state.state['infra_out'])
    
    # TAB 2: Observability
    with tabs[1]:
        st.subheader("🔭 OpenTelemetry Strategy")
        
        obs_mode = st.radio(
            "Choose OTel Pattern:",
            ["Universal Sidecar (K8s/Infra)", "SDK Implementation (Code-level)"],
            horizontal=True
        )
        
        c1, c2 = st.columns(2)
        
        if c1.button("🧪 Apply Telemetry", type="primary", use_container_width=True):
            if obs_mode == "Universal Sidecar (K8s/Infra)":
                if not st.session_state.state['infra_out']:
                    st.error("❌ No Infrastructure found! Generate K8s Manifests first.")
                else:
                    prompt = f"Inject an OpenTelemetry Collector sidecar into these K8s manifests: {st.session_state.state['infra_out']}. Use ---FILE: filename--- format."
                    st.session_state.state['infra_out'] = ask_ai(prompt)
                    st.rerun()
            else:
                prompt = f"Analyze these files: {st.session_state.state['selected_files']}. Rewrite them to implement OTel SDK. Use ---FILE: filename--- format."
                st.session_state.state['obs_out'] = ask_ai(prompt)
                st.rerun()
        
        if c2.button("📊 Gen Grafana/Prometheus", use_container_width=True):
            prompt = f"Generate Prometheus rules and Grafana dashboard for: {st.session_state.state['selected_files']}. Use ---FILE: filename--- format."
            st.session_state.state['obs_out'] = ask_ai(prompt)
            st.rerun()
        
        render_registry(st.session_state.state['obs_out'])
    
    # TAB 3: Security
    with tabs[2]:
        s1, s2 = st.columns(2)
        
        if s1.button("🛡️ Harden Security", use_container_width=True):
            prompt = f"Apply DevSecOps hardening (non-root, read-only fs, security contexts) to: {st.session_state.state['infra_out']}. Use ---FILE: filename--- format."
            st.session_state.state['infra_out'] = ask_ai(prompt)
            st.rerun()
        
        if s2.button("💰 FinOps Optimize", use_container_width=True):
            prompt = f"Optimize CPU/Memory requests and cloud costs for: {st.session_state.state['infra_out']}. Use ---FILE: filename--- format."
            st.session_state.state['infra_out'] = ask_ai(prompt)
            st.rerun()
    
    # TAB 4: Execution
    with tabs[3]:
        st.subheader("🚀 Command Execution")
        
        cmd = st.text_input(
            "Terminal Command:",
            value="ls -la",
            help="Allowed commands: " + ", ".join(Config.ALLOWED_COMMANDS)
        )
        
        col1, col2 = st.columns(2)
        
        if col1.button("💾 Save Generated Files", type="primary", use_container_width=True):
            saved_count = 0
            for fname, content in st.session_state.state['gen_cache'].items():
                try:
                    file_path = os.path.join(st.session_state.state['current_dir'], fname)
                    with open(file_path, 'w') as f:
                        f.write(content)
                    saved_count += 1
                    logger.info(f"Saved file: {fname}")
                except Exception as e:
                    st.error(f"Failed to save {fname}: {e}")
                    logger.error(f"File save error: {e}")
            
            if saved_count > 0:
                st.success(f"✅ Saved {saved_count} file(s) successfully!")
        
        if col2.button("🚀 Run Command", use_container_width=True):
            success, output = safe_execute_command(
                cmd,
                st.session_state.state['current_dir']
            )
            
            if success:
                st.success("✅ Command executed successfully")
            else:
                st.error("❌ Command failed")
            
            st.text_area("Output:", output, height=200)
    
    # TAB 5: Git Integration
    with tabs[4]:
        st.subheader("📊 Git Operations")
        
        # Initialize Git Manager if not exists
        if st.session_state.state['git_manager'] is None:
            st.session_state.state['git_manager'] = GitManager(
                st.session_state.state['current_dir']
            )
        
        git_mgr = st.session_state.state['git_manager']
        
        col1, col2, col3 = st.columns(3)
        
        if col1.button("📊 Status", use_container_width=True):
            success, status = git_mgr.get_status()
            if success:
                st.text_area("Repository Status:", status, height=150)
            else:
                st.error(status)
        
        if col2.button("📜 Log", use_container_width=True):
            success, log = git_mgr.get_log()
            if success:
                st.text_area("Commit History:", log, height=300)
            else:
                st.error(log)
        
        if col3.button("🔍 Diff", use_container_width=True):
            success, diff = git_mgr.get_diff()
            if success:
                st.code(diff, language="diff")
            else:
                st.error(diff)
        
        st.divider()
        
        # Commit section
        with st.expander("💾 Commit Changes"):
            commit_msg = st.text_area("Commit Message:", height=100)
            
            if st.button("✅ Stage & Commit", type="primary"):
                if not commit_msg:
                    st.error("Please provide a commit message")
                else:
                    # Stage generated files
                    files_to_stage = list(st.session_state.state['gen_cache'].keys())
                    if files_to_stage:
                        success, msg = git_mgr.add_files(files_to_stage)
                        if success:
                            success, msg = git_mgr.commit(commit_msg)
                            if success:
                                st.success(f"✅ {msg}")
                            else:
                                st.error(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("No files to commit")

# --- FOOTER ---
st.divider()
st.caption(f"🛡️ {Config.APP_NAME} {Config.APP_VERSION} | Secure • Modular • Enterprise-Ready")

# Made with Bob
