from rpython.rlib.objectmodel import specialize

class QuoppaException(Exception):
    def __init__(self, msg=None):
        if not msg:
            msg = ""
        self.msg = msg

class W_Object(object):
    __slots__ = []

    def to_string(self):
        return ''

    def to_repr(self):
        return "#<unknown>"

    def to_boolean(self):
        return True

    def __repr__(self):
        return "<" + self.__class__.__name__ + " " + self.to_string() + ">"

    def eq(self, w_obj):
        return self is w_obj

    eqv = eq
    equal = eqv

    def call(self, runtime, env, operative):
        raise QuoppaException("cannot call %s" % self.to_string())

class W_Undefined(W_Object):
    def to_repr(self):
        return "#<undefined>"

    to_string = to_repr

w_undefined = W_Undefined()

class W_True(W_Object):
    def to_repr(self):
        return "#t"
    to_string = to_repr

w_true = W_True()

class W_False(W_Object):
    def to_repr(self):
        return "#f"
    to_string = to_repr

    def to_boolean(self):
        return False

w_false = W_False()

class W_String(W_Object):
    def __init__(self, val):
        self.strval = val

    def to_string(self):
        return self.strval

    def to_repr(self):
        str_lst = ["\""]
        for ch in self.strval:
            if ch in ["\"", "\\"]:
                str_lst.append("\\" + ch)
            else:
                str_lst.append(ch)

        str_lst.append("\"")
        return ''.join(str_lst)

    def __repr__(self):
        return "<W_String \"" + self.strval + "\">"

    def equal(self, w_obj):
        if not isinstance(w_obj, W_String):
            return False
        return self.strval == w_obj.strval

class W_Symbol(W_Object):
    #class dictionary for symbol storage
    obarray = {}

    def __init__(self, val):
        self.name = val

    def to_repr(self):
        return self.name

    to_string = to_repr

def symbol(name):
    #use this to create new symbols, it stores all symbols
    #in W_Symbol.obarray dict
    #if already in obarray return it
    name = name.lower()
    w_symb = W_Symbol.obarray.get(name, None)
    if w_symb is None:
        w_symb = W_Symbol(name)
        W_Symbol.obarray[name] = w_symb

    assert isinstance(w_symb, W_Symbol)
    return w_symb

class W_Real(W_Object):
    def __init__(self, val):
        self.exact = False
        self.realval = val

    def to_string(self):
        return str(self.realval)

    def to_repr(self):
        # return repr(self.realval)
        return str(float(self.realval))

    def to_number(self):
        return self.to_float()

    def to_fixnum(self):
        return int(self.realval)

    def to_float(self):
        return self.realval

    def round(self):
        int_part = int(self.realval)
        if self.realval > 0:
            if self.realval >= (int_part + 0.5):
                return int_part + 1

            return int_part

        else:
            if self.realval <= (int_part - 0.5):
                return int_part - 1

            return int_part

    def is_integer(self):
        return self.realval == self.round()

    def eqv(self, w_obj):
        return isinstance(w_obj, W_Real) \
            and self.exact is w_obj.exact \
            and self.realval == w_obj.realval
    equal = eqv

W_Number = W_Real

class W_Integer(W_Real):
    def __init__(self, val):
        self.intval = val
        self.realval = val
        self.exact = True

    def to_string(self):
        return str(self.intval)

    def to_repr(self):
        #return repr(self.intval)
        return str(int(self.intval))

    def to_number(self):
        return self.to_fixnum()

    def to_fixnum(self):
        return self.intval

    def to_float(self):
        return float(self.intval)

class W_EofObject(W_Object):
    pass
w_eof = W_EofObject()

class W_Stream(W_Object):
    def __init__(self, filename):
        from rpython.rlib.streamio import open_file_as_stream
        self.filename = filename
        self.contents = open_file_as_stream(filename, buffering=0).readall()
        self.sexprs = None
        self.sexpr_pos = 0

    def to_string(self):
        return "#<FileStream #{%s}>" % self.filename
    to_repr = to_string

    def next_sexpr(self):
        if self.sexprs and self.sexpr_pos < len(self.sexprs):
            sexpr = self.sexprs[self.sexpr_pos]
            self.sexpr_pos += 1
            return sexpr
        else:
            return w_eof

class W_List(W_Object):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def to_string(self):
        return "(" + self.to_lstring() + ")"

    def to_lstring(self):
        car = self.car.to_string()
        cdr = self.cdr
        if cdr is w_nil:
            return car
        elif isinstance(cdr, W_List): #still proper list
            return car + " " + cdr.to_lstring()
        else: #end proper list with dotted
            return car + " . " + cdr.to_string()

    def to_repr(self):
        return "(" + self.to_lrepr() + ")"

    def to_lrepr(self):
        car = self.car.to_repr()
        cdr = self.cdr
        if cdr is w_nil: #end of proper list
            return car
        elif isinstance(cdr, W_List): #still proper list
            return car + " " + cdr.to_lrepr()
        else: #end proper list with dotted
            return car + " . " + cdr.to_repr()

    def __repr__(self):
        return "<W_List " + self.to_repr() + ">"

    def equal(self, w_obj):
        return isinstance(w_obj, W_List) and \
            self.car.equal(w_obj.car) and \
            self.cdr.equal(w_obj.cdr)

    def cons(self, w_pair):
        if self.cdr is w_nil:
            return W_List(self.car, w_pair)
        else:
            return W_List(self.car, self.cdr.cons(w_pair))

    def comma(self, w_pair):
        if self.cdr is w_nil:
            self.cdr = w_pair
            return self
        else:
            self.cdr.comma(w_pair)
            return self

def w_list(first, *args):
    w_l = W_List(first, w_nil)
    for w_item in list(args):
        w_l.comma(W_List(w_item, w_nil))
    return w_l

class W_Nil(W_List):
    _w_nil = None
    def __new__(cls):
        if cls._w_nil is None:
            cls._w_nil = W_Object.__new__(cls)
        return cls._w_nil

    def __init__(self):
        pass

    def __repr__(self):
        return "<W_Nil ()>"

    def to_repr(self):
        return "()"

    to_string = to_repr

    def comma(self, w_pair):
        return w_pair

    cons = comma

w_nil = W_Nil()

class W_Fexpr(W_Object):
    def __init__(self, env_param, params, static_env, body):
        self.env_param = env_param
        self.params = params
        self.static_env = static_env
        self.body = body

    def to_string(self):
        return '#<an fexpr>'

    to_repr = to_string

    def call(self, runtime, dynamic_env, operands):
        local_names = W_List(self.env_param, self.params)
        local_values = W_List(dynamic_env, operands)
        local_env = W_List(runtime.bind(local_names, local_values), self.static_env)
        return runtime.m_eval(local_env, self.body)

class W_Primitive(W_Fexpr):
    @specialize.memo()
    def __init__(self, fun):
        code = fun.__code__

        lines = []
        lines.append("def %s(args_w):" % fun.__name__)
        lines.append("    args = ()")

        arg_count = 0
        for i, argname in enumerate(code.co_varnames[:code.co_argcount]):
            if argname != "self":
                coerce_code = "args_w[{:d}]".format(arg_count)
                lines.append("    if len(args_w) > {}:".format(arg_count))
                lines.append("        args += ({},)".format(coerce_code))
                lines.append("    else:")
                lines.append("        raise Exception({}, '{}')".format(i, argname))
                arg_count += 1
        lines.append("    return func(*args)")

        source = "\n".join(lines)
        namespace = {"func": fun}
        exec source in namespace
        self.fun = namespace[fun.__name__]

    def to_string(self):
        return "#<a primitive>"

    to_repr = to_string

    def call(self, runtime, env, operands):
        operands_w = []
        while operands is not w_nil:
            assert isinstance(operands, W_List)
            operands_w.append(runtime.m_eval(env, operands.car))
            operands = operands.cdr
        return self.fun(operands_w)

class W_Vau(W_Primitive):
    def call(self, runtime, env, operands):
        return self.fun([env, operands])
