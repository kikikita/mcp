echo "=== 1) Запуск MCP-сервера (mcp_server.py) на порту 9000 ==="
nohup uvicorn mcp_server:app --host 0.0.0.0 --port 9000 > mcp_server.log 2>&1 &
MCP_PID=$!
echo "MCP-сервер запущен с PID = $MCP_PID  (логи: mcp_server.log)"

sleep 2

echo
echo "=== 2) Запуск LLM-сервера (llm_server.py) на порту 8022 ==="
nohup uvicorn llm_server:app --host 0.0.0.0 --port 8022 > llm_server.log 2>&1 &
LLM_PID=$!
echo "LLM-сервер запущен с PID = $LLM_PID  (логи: llm_server.log)"

sleep 2

echo "=== 3) Запуск MCP-клиента (mcp_сlient.py) на порту 8021 ==="
nohup uvicorn mcp_client:app --host 0.0.0.0 --port 8021 > mcp_client.log 2>&1 &
MCPc_PID=$!
echo "MCP-сервер запущен с PID = $MCPc_PID  (логи: mcp_client.log)"

sleep 2

echo
echo "=== СЕРВИСЫ ЗАПУЩЕНЫ ==="
echo "  • MCP-сервер (порт 9000)  PID = $MCP_PID"
echo "  • LLM-сервер (порт 8022)  PID = $LLM_PID"
echo "  • MCP-клиента (порт 8021)  PID = $MCPc_PID"
echo "  • Результаты теста MCP-клиента  → mcp_client.log"
echo
echo "Чтобы остановить все сервера, выполните:"
echo "  kill $MCP_PID $LLM_PID $MCPc_PID"