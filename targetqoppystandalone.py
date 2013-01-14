#!/usr/bin/env python
import sys, traceback, os

from pypy.rlib.objectmodel import specialize
from pypy.rlib.streamio import open_file_as_stream
from pypy.rlib.parsing.makepackrat import BacktrackException

from qoppy.runtime import Runtime, get_runtime
from qoppy.execution_model import QuoppaException


def entry_point(argv):
    if len(argv) == 2:
        runtime = get_runtime()
        code = open_file_as_stream(argv[1]).readall()
        try:
            runtime.execute(code)
        except BacktrackException, e:
            (line, col) = e.error.get_line_column(code)
            print "parse error in line %d, column %d" % (line, col)
            return 1
        except QuoppaException as e:
            os.write(1, "%s\n" % str(e))
            os.write(1, "%s\n" % str(e.msg))
            return 1
        return 0
    else:
        print "Usage: %s [quoppa source file]" % argv[0]
        return 1

def target(driver, *args):
    driver.exe_name = 'qoppy-%(backend)s'
    return entry_point, None

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

if __name__ == "__main__":
    entry_point(sys.argv)
