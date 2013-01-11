from qoppy.runtime import get_runtime
from qoppy.parser import parse
from qoppy.execution_model import *

r = get_runtime()

def test_primitives():
    w_res = r.interpret(w_nil, parse("1")[0])
    assert isinstance(w_res, W_Integer)

    w_res = r.interpret(w_nil, parse("nil")[0])
    assert w_res is w_nil

    w_res = r.interpret(w_nil, parse('"foo"')[0])
    assert isinstance(w_res, W_String)

    w_res = r.interpret(w_nil, parse('barf')[0])
    assert isinstance(w_res, W_Symbol)

    w_res = r.interpret(w_nil, parse("1.1")[0])
    assert isinstance(w_res, W_Real)

    #    w_res = r.interpret(w_nil, parse("")[0])
    #    assert isinstance(w_res, W_Integer)
    


