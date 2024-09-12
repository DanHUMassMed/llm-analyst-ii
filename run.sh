#!/bin/bash
# Get the active conda environment
active_env=$(conda info | egrep "active environment" | cut -d: -f2 | tr -d '[:space:]')

# Check if the active environment is "fastAPI"
if [ "$active_env" != "llm-analyst-web" ]; then
    logger "You are not in the 'llm-analyst-web' environment. Activating it now..."
    
    # Activate the 'fastAPI' environment
    source /home/dan/miniconda3/bin/activate llm-analyst-web
    
    # Confirm activation
    if [ $(conda info | egrep "active environment" | cut -d: -f2 | tr -d '[:space:]') == "fastAPI" ]; then
        logger "Environment 'llm-analyst-web' activated successfully."
    else
        logger "Failed to activate 'llm-analyst-web' environment."
    fi
else
    logger "You are already in the 'llm-analyst-web' environment."
fi

#uvicorn app.main:app --host 0.0.0.0 --reload
cd /home/dan/Code/LLM_Code/llm-analyst-web
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000

