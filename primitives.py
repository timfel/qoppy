import os

from execution_model import w_nil, W_Real, W_Boolean, W_Symbol, W_List, QuoppaException

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

def cons(w_car, w_cdr):
    return W_List(w_car, w_cdr)

def car(w_pair):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        return w_pair.car
    else:
        raise QuoppaException("wrong type argument %s for car" % w_pair)

def cdr(w_pair):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        return w_pair.car
    else:
        raise QuoppaException("wrong type argument %s for cdr" % w_pair)

def set_car_b(w_pair, w_val):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        w_pair.car = w_val
        return w_pair
    else:
        raise QuoppaException("wrong type argument %s for set-car!" % w_pair)

def set_cdr_b(w_pair, w_val):
    if isinstance(w_pair, W_List) and w_pair is not w_nil:
        w_pair.cdr = w_val
        return w_pair
    else:
        raise QuoppaException("wrong type argument %s for set-cdr!" % w_pair)

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

def error(w_msg = None):
    if w_msg is None:
        msg = ""
    else:
        msg = w_msg.to_string()
    raise QuoppaException(msg)

def display(w_str):
    os.write(1, w_str.to_string())
    return w_nil
