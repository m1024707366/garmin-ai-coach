import sys
import os

print("Python version:", sys.version)
print("\nPython path:", sys.path)
print("\nCurrent directory:", os.getcwd())
print("\nFiles in current directory:")
for item in sorted(os.listdir("/app")):
    print(f"  {item}")

try:
    print("\nTrying to import backend...")
    import backend
    print("Successfully imported backend")
except ImportError as e:
    print(f"Failed to import backend: {e}")
