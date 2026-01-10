@echo off
cd /d D:\Project\lambadaFunction

lambdaenv\Scripts\python.exe -m streamlit run app.py ^
  --server.port 8501 ^
  --server.headless true
