import os

file_path = os.path.expanduser("~/vllm_env/lib64/python3.11/site-packages/transformers/models/qwen2_5_vl/configuration_qwen2_5_vl.py")

with open(file_path, "r") as f:
    content = f.read()

# Add properties to the end of Qwen2_5_VLConfig class
class_def = "class Qwen2_5_VLConfig(PretrainedConfig):"
properties = """
    @property
    def pad_token_id(self):
        return getattr(self, "_pad_token_id", 151643)

    @pad_token_id.setter
    def pad_token_id(self, value):
        self._pad_token_id = value

    @property
    def vocab_size(self):
        return 152064

    @vocab_size.setter
    def vocab_size(self, value):
        pass

    @property
    def hidden_size(self):
        return 3584

    @hidden_size.setter
    def hidden_size(self, value):
        pass

    @property
    def num_attention_heads(self):
        return 28

    @num_attention_heads.setter
    def num_attention_heads(self, value):
        pass

    @property
    def num_key_value_heads(self):
        return 4
        
    @num_key_value_heads.setter
    def num_key_value_heads(self, value):
        pass
"""

if "def pad_token_id(self):" not in content:
    # Find the end of __init__ method to insert properties
    # Just insert it before the end of the class
    # Actually, simpler: replace the class definition line and add it right after
    content = content.replace(
        "class Qwen2_5_VLConfig(PretrainedConfig):",
        "class Qwen2_5_VLConfig(PretrainedConfig):\n" + properties
    )
    with open(file_path, "w") as f:
        f.write(content)
    print("Qwen2_5_VLConfig patched!")
else:
    print("Qwen2_5_VLConfig already patched.")
