import torch
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_PATH = os.path.join(PROJECT_ROOT, "legacy_model_pipeline", "outputs", "twohead", "best.pt")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "legacy_model_pipeline", "outputs", "twohead", "best_inference.pt")

print("Loading checkpoint...")
ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")

print("Checkpoint type:", type(ckpt))

# Extract only model weights
if isinstance(ckpt, dict):

    if "model_state_dict" in ckpt:
        print("Found: model_state_dict")
        weights = ckpt["model_state_dict"]

    elif "state_dict" in ckpt:
        print("Found: state_dict")
        weights = ckpt["state_dict"]

    else:
        print("No explicit state_dict found.")
        print("Saving full dict as fallback.")
        weights = ckpt

else:
    print("Checkpoint already appears to be raw weights.")
    weights = ckpt

print("Saving lightweight inference checkpoint...")
torch.save(weights, OUTPUT_PATH)

old_size = os.path.getsize(CHECKPOINT_PATH) / (1024 * 1024)
new_size = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)

print(f"\nOld size: {old_size:.2f} MB")
print(f"New size: {new_size:.2f} MB")

print("\nInference checkpoint exported successfully!")
