"""Build a fixed ONNX graph shaped like one transformer encoder block.

The property under test is NOT a particular model: it is whether onnxruntime's
float32 kernels for the ops a cross-encoder is made of produce bit-identical
output on x86-64 and aarch64. Weights and input are generated once, here, and
shipped as files, so both machines run identical bytes.
"""
import numpy as np, onnx
from onnx import helper, TensorProto as TP

rng = np.random.default_rng(20260824)
S, H, F = 128, 384, 1536          # MiniLM-L6 shapes: seq 128, hidden 384, ffn 1536
def w(*shape): return rng.standard_normal(shape).astype(np.float32) * 0.05

Wq, Wk, Wv, Wo = w(H,H), w(H,H), w(H,H), w(H,H)
W1, W2 = w(H,F), w(F,H)
g1, b1 = np.ones(H, np.float32), np.zeros(H, np.float32)

init = [helper.make_tensor(n, TP.FLOAT, list(a.shape), a.ravel().tolist())
        for n, a in [("Wq",Wq),("Wk",Wk),("Wv",Wv),("Wo",Wo),("W1",W1),("W2",W2),("g1",g1),("b1",b1)]]
scale = helper.make_tensor("scale", TP.FLOAT, [], [1.0/np.sqrt(H/6).astype(np.float32).item()])
init.append(scale)

N = helper.make_node
nodes = [
    N("MatMul", ["x","Wq"], ["q"]), N("MatMul", ["x","Wk"], ["k"]), N("MatMul", ["x","Wv"], ["v"]),
    N("Transpose", ["k"], ["kt"], perm=[1,0]),
    N("MatMul", ["q","kt"], ["qk"]),
    N("Mul", ["qk","scale"], ["qks"]),
    N("Softmax", ["qks"], ["att"], axis=-1),
    N("MatMul", ["att","v"], ["ctx"]),
    N("MatMul", ["ctx","Wo"], ["proj"]),
    N("Add", ["proj","x"], ["res"]),
    N("LayerNormalization", ["res","g1","b1"], ["ln"], axis=-1, epsilon=1e-12),
    N("MatMul", ["ln","W1"], ["h1"]),
    N("Gelu", ["h1"], ["h2"]),
    N("MatMul", ["h2","W2"], ["h3"]),
    N("Add", ["h3","ln"], ["out"]),
    N("ReduceMean", ["out"], ["pooled"]),   # a single relevance-like scalar
]
graph = helper.make_graph(nodes, "encoder_block",
    [helper.make_tensor_value_info("x", TP.FLOAT, [S,H])],
    [helper.make_tensor_value_info("out", TP.FLOAT, [S,H]),
     helper.make_tensor_value_info("pooled", TP.FLOAT, [1,1])],
    init)
m = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 20)])
m.ir_version = 10
onnx.checker.check_model(m)
onnx.save(m, "block.onnx")

x = (rng.standard_normal((S,H)).astype(np.float32) * 0.3)
x.tofile("input.f32")
print("wrote block.onnx", round(len(m.SerializeToString())/1e6,2), "MB; input.f32", x.nbytes, "bytes")
