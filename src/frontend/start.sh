#!/bin/bash

# Start Metadata Server in background
python src/frontend/metadata_server.py &

# Start Streamlit
streamlit run src/frontend/app.py --server.port=8501 --server.address=0.0.0.0
