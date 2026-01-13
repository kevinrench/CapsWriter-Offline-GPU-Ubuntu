import time
import sherpa_onnx
from config import ParaformerArgs

print("Testing model loading with settings:")
args = {key: value for key, value in ParaformerArgs.__dict__.items() if not key.startswith('_')}
print(args)

try:
    recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(**args)
    print("Successfully loaded model on", args.get('provider', 'default'))
except Exception as e:
    print("Failed to load model:", e)
