FROM ollama/ollama:latest

# 啟動 Ollama 背景服務，等佢 Ready 之後，自動 Pull 模型
RUN nohup bash -c "ollama serve &" && sleep 5 && ollama pull translategemma:4b-it-q4_K_M