
import sounddevice as sd
try:
    device = sd.query_devices(kind='input')
    print(f"Selected Device: {device['name']}")
    print(f"Index: {device['index']}")
except Exception as e:
    print(e)
