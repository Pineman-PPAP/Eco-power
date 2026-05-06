import sys
import time

def trace_import(module_name):
    print(f"Importing {module_name}...", end="", flush=True)
    start = time.time()
    try:
        __import__(module_name)
        print(f" DONE ({time.time() - start:.2f}s)")
    except Exception as e:
        print(f" FAILED: {e}")

print("--- Tracing Imports ---")
trace_import("pandas")
trace_import("numpy")
trace_import("fastapi")
trace_import("lightgbm")
trace_import("joblib")
trace_import("src.data.loader")
trace_import("src.data.cleaner")
trace_import("src.features.engineering")
trace_import("src.models.train")
trace_import("src.models.predict")
trace_import("src.models.explainability")
print("--- Trace Complete ---")
