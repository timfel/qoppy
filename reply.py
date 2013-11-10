#!/usr/bin/env python
import sys, traceback, os

from rpython.rlib.objectmodel import specialize
from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.makepackrat import BacktrackException

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

def check_parens(s):
    return s.count("(") == s.count(")")

def interactive():
    print "PyPy Qoppa interpreter"
    runtime = get_runtime()
    to_exec = ""
    cont = False
    while 1:
        if cont:
            ps = '.. '
        else:
            ps = '-> '
        sys.stdout.write(ps)
        to_exec += sys.stdin.readline()
        if to_exec == "\n":
            to_exec = ""
        elif check_parens(to_exec):
            try:
                if to_exec == "":
                    print
                    exit(0)
                print runtime.m_eval(w_nil, parse(to_exec)[0])
            except QuoppaException as e:
                os.write(1, "%s\n" % str(e))
                os.write(1, "%s\n" % str(e.msg))
                traceback.print_tb(sys.exc_info()[2], 10)
            except BacktrackException as e:
                (line, col) = e.error.get_line_column(to_exec)
                expected = " ".join(e.error.expected)
                print "parse error: in line %s, column %s expected: %s" % \
                        (line, col, expected)
            except Exception, e:
                os.write(1, "%s\n" % str(e))
                traceback.print_tb(sys.exc_info()[2], 10)
            to_exec = ""
            cont = False
        else:
            cont = True

if __name__ == '__main__':
    interactive()
