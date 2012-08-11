import os

from runtime import w_nil, W_Real, W_Boolean, W_Symbol, W_List, QuoppaException

def m_bool(b, t, f):
    if b.to_boolean():
        return t
    else:
        return f

def eq_p(a, b):
    return W_Boolean(a.equal(b))

def null_p(o):
    return W_Boolean(o is w_nil)

def symbol_p(o):
    return W_Boolean(isinstance(o, W_Symbol))

def pair_p(o):
    return W_Boolean(isinstance(o, W_List))

def cons(w_pair, w_other):
    return w_pair.cons(w_other)

def car(w_pair):
    return w_pair.car

def cdr(w_pair):
    return w_pair.cdr

def set_car_b(w_pair, w_val):
    car = w_pair.car
    cdr = w_pair.cdr
    w_pair.car = w_val
    w_pair.cdr = W_List(car, cdr)
    return w_pair

def set_cdr_b(w_pair, w_val):
    w_pair.cdr = w_val
    return w_pair

def plus(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() + b.to_number())
    else:
        raise QuoppaException("cannot %s + %s" % (a, b))

def times(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() * b.to_number())
    else:
        raise QuoppaException("cannot %s * %s" % (a, b))

def minus(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() - b.to_number())
    else:
        raise QuoppaException("cannot %s - %s" % (a, b))

def div(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Real(a.to_number() / b.to_number())
    else:
        raise QuoppaException("cannot %s / %s" % (a, b))

def less_or_eq(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Boolean(a.to_number() <= b.to_number())
    else:
        raise QuoppaException("cannot %s <= %s" % (a, b))

def eq(a, b):
    if isinstance(a, W_Real) and isinstance(b, W_Real):
        return W_Boolean(a.to_number() == b.to_number())
    else:
        return W_Boolean(a.equal(b))

def error(msg = None):
    if msg is None:
        msg = ""
    raise QuoppaException(msg)

def display(w_str):
    os.write(1, w_str.to_string())
    return w_nil
