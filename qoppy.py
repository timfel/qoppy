#!/usr/bin/env python
import sys, traceback, os

from pypy.rlib.objectmodel import specialize
from pypy.rlib.streamio import open_file_as_stream
from pypy.rlib.parsing.makepackrat import BacktrackException

from parser import parse
from runtime import Runtime
from execution_model import w_nil, QuoppaException

@specialize.memo()
def get_runtime():
    from primitives import (m_bool, eq_p, null_p, symbol_p, pair_p, cons,
                            car, cdr, set_car_b, set_cdr_b, plus, times, minus,
                            div, less_or_eq, eq, error, display,
                            read, eof_object_p, open_input_file)
    return Runtime({
            "bool": m_bool,
            "eq?": eq_p,
            "null?": null_p,
            "symbol?": symbol_p,
            "pair?": pair_p,
            "cons": cons,
            "car": car,
            "cdr": cdr,
            "set-car!": set_car_b,
            "set-cdr!": set_cdr_b,
            "+": plus,
            "*": times,
            "-": minus,
            "/": div,
            "<=": less_or_eq,
            "=": eq,
            "error": error,
            "display": display,
            "read": read,
            "eof-object?": eof_object_p,
            "open-input-file": open_input_file
    })

def entry_point(argv):
    if len(argv) == 2:
        runtime = get_runtime()
        code = open_file_as_stream(argv[1]).readall()
        try:
            t = parse(code)
        except BacktrackException, e:
            (line, col) = e.error.get_line_column(code)
            print "parse error in line %d, column %d" % (line, col)
            return 1

        for sexpr in t:
            try:
                runtime.interpret(w_nil, sexpr)
            except QuoppaException as e:
                os.write(1, "%s\n" % str(e))
                os.write(1, "%s\n" % str(e.msg))
                # import pdb; pdb.set_trace()
                # traceback.print_tb(sys.exc_info()[2])
                return 1
        return 0
    else:
        print "Usage: %s [quoppa source file]" % argv[0]
        return 1

def target(*args):
    return entry_point, None

if __name__ == "__main__":
    entry_point(sys.argv)
