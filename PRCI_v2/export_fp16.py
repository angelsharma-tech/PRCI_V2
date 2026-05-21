import torch
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(PROJECT_ROOT, "legacy_model_pipeline", "outputs", "twohead", "best.pt")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "legacy_model_pipeline", "outputs", "twohead", "best_fp16.pt")

print("Loading checkpoint...")
ckpt = torch.load(INPUT_PATH, map_location="cpu")

# Extract state_dict if wrapped
if isinstance(ckpt, dict) and "state_dict" in ckpt:
    state_dict = ckpt["state_dict"]
    print("Unwrapped state_dict from checkpoint.")
else:
    state_dict = ckpt
    print("Using raw checkpoint (already state_dict).")

print("Converting to FP16...")

fp16_state_dict = {}

for k, v in state_dict.items():
    if torch.is_tensor(v):
        fp16_state_dict[k] = v.half()
    else:
        fp16_state_dict[k] = v

print("Saving FP16 checkpoint...")
torch.save(fp16_state_dict, OUTPUT_PATH)

old_size = os.path.getsize(INPUT_PATH) / (1024 * 1024)
new_size = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)

print(f"\nOld size: {old_size:.2f} MB")
print(f"New size: {new_size:.2f} MB")

print("\nFP16 checkpoint exported successfully!")
