#!/bin/sh 
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install streamlit ollama
pip install watchdog
pip install streamlit ollama google-generativeai mistralai python-dotenv cryptography
pip install -r requirements.txt

####
python3.12 -m venv myenv
source myenv/bin/activate
####

## uv
# curl -LsSf https://astral.sh/uv/install.sh | sh
# uv venv --python 3.12.4 
# uv run python my_script.py
uv venv my-custom-env
source my-custom-env/bin/activate
uv pip install -r requirements.txt