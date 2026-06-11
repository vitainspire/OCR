import os

file_path = os.path.expanduser("~/vllm_env/lib64/python3.11/site-packages/transformers/integrations/finegrained_fp8.py")

with open(file_path, 'r') as f:
    content = f.read()

content = content.replace("torch.float8_e8m0fnu", "getattr(torch, 'float8_e8m0fnu', None)")

with open(file_path, 'w') as f:
    f.write(content)
print("Patch applied!")
