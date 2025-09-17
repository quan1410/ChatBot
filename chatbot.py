from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType
import torch
from transformers import BitsAndBytesConfig

checkpoint_dir = "./kaggle/vistral-law-finetuned/finetuned_model"

model = AutoModelForCausalLM.from_pretrained(checkpoint_dir)
tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)

# Áp dụng LoRA (nếu có)
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=True,  # Chế độ inference (không fine-tune thêm)
    r=16,
    lora_alpha=32,
    lora_dropout=0.1
)

model = get_peft_model(model, peft_config)
model.eval()  # Chuyển mô hình về chế độ inference

input_text = "Chào bạn, hôm nay bạn cảm thấy như thế nào?"

# Tokenize input
inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

# Sinh văn bản
output = model.generate(inputs['input_ids'], max_length=150, num_return_sequences=1)

# Chuyển kết quả từ id thành văn bản
generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

print("Generated text:", generated_text)
