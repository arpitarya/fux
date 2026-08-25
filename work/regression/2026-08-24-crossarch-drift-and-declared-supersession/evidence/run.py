"""Run the fixed graph and emit a machine-independent fingerprint.

Single-threaded and with graph optimisation DISABLED where it matters, so the
comparison is of kernels rather than of whichever fusion each build chose.
"""
import hashlib, platform, sys
import numpy as np, onnxruntime as ort

S, H = 128, 384
x = np.fromfile("input.f32", dtype=np.float32).reshape(S, H)

so = ort.SessionOptions()
so.intra_op_num_threads = 1
so.inter_op_num_threads = 1
so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL

sess = ort.InferenceSession("block.onnx", so, providers=["CPUExecutionProvider"])
out, pooled = sess.run(["out", "pooled"], {"x": x})

print(f"machine   {platform.machine()}")
print(f"ort       {ort.__version__}")
print(f"python    {platform.python_version()}")
print(f"out.sha256 {hashlib.sha256(out.tobytes()).hexdigest()}")
print(f"pooled     {pooled.ravel()[0]!r}")
print(f"pooled.hex {pooled.ravel()[0].tobytes().hex()}")
out.astype(np.float32).tofile("out.f32")
