from qoppy.runtime import get_runtime
from qoppy.parser import parse
from qoppy.execution_model import w_nil, QuoppaException

r = get_runtime()

def test_primitives():
    r.interpret(w_nil, parse("(1)"))


