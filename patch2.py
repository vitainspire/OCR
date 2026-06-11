import os

file_path = os.path.expanduser("~/vllm_env/lib64/python3.11/site-packages/vllm/transformers_utils/tokenizer.py")

with open(file_path, 'r') as f:
    content = f.read()

content = content.replace("tokenizer.all_special_tokens_extended", "getattr(tokenizer, 'all_special_tokens_extended', [])")

with open(file_path, 'w') as f:
    f.write(content)
print("vLLM Tokenizer patch applied!")
