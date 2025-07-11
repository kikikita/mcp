MODEL="Salesforce/xLAM-2-32b-fc-r"
MODEL2="Salesforce/Llama-xLAM-2-70b-fc-r"
MODEL3="Salesforce/Llama-xLAM-2-8b-fc-r"

nohup vllm serve "$MODEL" \
  --enable-auto-tool-choice \
  --tool-parser-plugin ./xlam_tool_call_parser.py \
  --tool-call-parser xlam \
  --tensor-parallel-size 2
