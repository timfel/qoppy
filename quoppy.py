#!/usr/bin/env python
import sys

from pypy.rlib.streamio import open_file_as_stream
from pypy.rlib.parsing.makepackrat import BacktrackException

from parser import parse
from runtime import (W_List, symbol, w_nil, W_Primitive, W_Vau,
                     vau, m_eval, operate, lookup)
# from primitives import (
#     m_bool, eq_p, null_p, symbol_p, pair_p, cons, car, cdr,
#     set_car_b, set_cdr_b, plus, times, minus, div, less_or_eq,
#     eq, error, display, read, eof_object_p, open_input_file)


def make_global_frame():
    frame = W_List(W_List(symbol("vau"), W_Vau(vau)), w_nil)
    for prim in ([["eval", W_Primitive(m_eval)],
                  ["operate", W_Primitive(operate)],
                  ["lookup", W_Primitive(lookup)],
                  # ["bool", W_Primitive(m_bool)],
                  # ["eq?", W_Primitive(eq_p)],
                  # ["null?", W_Primitive(null_p)],
                  # ["symbol?", W_Primitive(symbol_p)],
                  # ["pair?", W_Primitive(pair_p)],
                  # ["cons", W_Primitive(cons)],
                  # ["car", W_Primitive(car)],
                  # ["cdr", W_Primitive(cdr)],
                  # ["set-car!", W_Primitive(set_car_b)],
                  # ["set-cdr!", W_Primitive(set_cdr_b)],
                  # ["+", W_Primitive(plus)],
                  # ["*", W_Primitive(times)],
                  # ["-", W_Primitive(minus)],
                  # ["/", W_Primitive(div)],
                  # ["<=", W_Primitive(less_or_eq)],
                  # ["=", W_Primitive(eq)],
                  # ["error", W_Primitive(error)],
                  # ["display", W_Primitive(display)],
                  # ["read", W_Primitive(read)],
                  # ["eof-object?", W_Primitive(eof_object_p)],
                  # ["open-input-file", W_Primitive(open_input_file)]
                  ]):
        frame.comma(W_List(W_List(symbol(prim[0]), prim[1]), w_nil))
    return frame

global_env = make_global_frame()

def entry_point(argv):
    if len(argv) == 2:
        code = open_file_as_stream(argv[1]).readall()
        try:
            t = parse(code)
        except BacktrackException, e:
            (line, col) = e.error.get_line_column(code)
            print "parse error in line %d, column %d" % (line, col)
            return 1

        #this should not be necessary here
        assert isinstance(t, list)
        for sexpr in t:
            print sexpr
            w_retval = m_eval(global_env, sexpr)
            print w_retval.to_string()
        return 0
    else:
        print "Usage: %s [quoppa source file]" % argv[0]
        return 1

def target(*args):
    return entry_point, None

if __name__ == "__main__":
    entry_point(sys.argv)
