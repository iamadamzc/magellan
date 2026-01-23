@echo off
REM Scanner Launcher - Double-click to start
cd /d "A:\1\scanner"
start "" "http://localhost:8501"
streamlit run app.py
