from qoppy.runtime import get_runtime
from qoppy.execution_model import *

r = get_runtime()

def test_primitives():
    w_res = r.execute("1")
    assert isinstance(w_res, W_Integer)

    w_res = r.execute("nil")
    assert w_res is w_nil

    w_res = r.execute('"foo"')
    assert isinstance(w_res, W_String)

    w_res = r.execute("1.1")
    assert isinstance(w_res, W_Real)

def test_eval():
    w_res = r.execute("(eval nil 1)")
    assert isinstance(w_res, W_Integer)
