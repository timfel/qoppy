import os

from execution_model import (w_nil, w_true, w_false, W_Real,
                             W_Symbol, W_List, QuoppaException,
                             W_Stream)

def m_bool(b, t, f):
    if b.to_boolean():
        return t
    else:
        return f

def eq_p(a, b):
    if a.equal(b):
        return w_true
    else:
        return w_false

def null_p(w_obj):
    if w_obj is w_nil:
        return w_true
    else:
        return w_false

def symbol_p(w_obj):
    if isinstance(w_obj, W_Symbol):
        return w_true
    else:
        return w_false

def pair_p(w_obj):
    if isinstance(w_obj, W_List):
        return w_true
    else:
        return w_false

def cons(w_car, w_cdr):
    return W_List(w_car, w_cdr)

def car(w_pair):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        return w_pair.car
    else:
        raise QuoppaException("wrong type argument %s for car" % w_pair.to_string())

def cdr(w_pair):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        return w_pair.cdr
    else:
        raise QuoppaException("wrong type argument %s for cdr" % w_pair.to_string())

def set_car_b(w_pair, w_val):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        w_pair.car = w_val
        return w_pair
    else:
        raise QuoppaException("wrong type argument %s for set-car!" % w_pair.to_string())

def set_cdr_b(w_pair, w_val):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        w_pair.cdr = w_val
        return w_pair
    else:
        raise QuoppaException("wrong type argument %s for set-cdr!" % w_pair.to_string())

def plus(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() + b.to_number())
    else:
        raise QuoppaException("cannot %s + %s" % (a.to_string(), b.to_string()))

def times(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() * b.to_number())
    else:
        raise QuoppaException("cannot %s * %s" % (a.to_string(), b.to_string()))

def minus(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() - b.to_number())
    else:
        raise QuoppaException("cannot %s - %s" % (a.to_string(), b.to_string()))

def div(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() / b.to_number())
    else:
        raise QuoppaException("cannot %s / %s" % (a.to_string(), b.to_string()))

def less_or_eq(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        if a.to_number() <= b.to_number():
            return w_true
        else:
            return w_false
    else:
        raise QuoppaException("cannot %s <= %s" % (a.to_string(), b.to_string()))

def eq(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        test = a.to_number() == b.to_number()
    else:
        test = a.equal(b)
    if test:
        return w_true
    else:
        return w_false

def error(w_msg = None):
    if w_msg is None:
        msg = ""
    else:
        msg = w_msg.to_string()
    raise QuoppaException(msg)

def display(w_str):
    os.write(1, w_str.to_string())
    return w_nil

def read(w_stream):
    if isinstance(w_stream, W_Stream):
        os.read(w_stream.fd, 1)
    else:
        raise QuoppaException("cannot read from %r" % w_stream)

def eof_object_p(w_obj):
    if isinstance(w_obj, W_String) and str(w_obj) == "":
        return w_true
    else:
        return w_false

def open_input_file(w_str):
    pass
