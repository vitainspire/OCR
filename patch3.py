import os

file_path = os.path.expanduser("~/vllm_env/lib64/python3.11/site-packages/vllm/model_executor/models/qwen2.py")

with open(file_path, 'r') as f:
    content = f.read()

content = content.replace("self.padding_idx = config.pad_token_id", "self.padding_idx = getattr(config, 'pad_token_id', 151643)")

with open(file_path, 'w') as f:
    f.write(content)
print("vLLM Qwen2 model pad_token_id patch applied!")
