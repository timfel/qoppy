from pypy.rlib import jit
from pypy.rlib.objectmodel import specialize

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

    def compile(self, runtime, env_stack, stack, operand_stack):
        return env_stack, W_List(self, stack), operand_stack

    def is_nil(self):
        return False


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

    def compile(self, runtime, env_stack, stack, operand_stack):
        cdr = runtime.lookup(self, env_stack.car).cdr
        assert isinstance(cdr, W_List) and cdr is not w_nil
        return env_stack, W_List(cdr.car, stack), operand_stack

    def equal(self, w_obj):
        return self is w_obj


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
        from pypy.rlib.streamio import open_file_as_stream
        self.filename = filename
        self.contents = open_file_as_stream(filename).readall()
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
        if cdr.is_nil():
            return car
        elif isinstance(cdr, W_List): #still proper list
            return car + " " + cdr.to_lstring()
        else: #end proper list with dotted
            return car + " . " + cdr.to_string()

    def to_array(self):
        ary = []
        l = self
        while l is not w_nil:
            assert isinstance(l, W_List)
            l.append(l.car)
            l.cdr
        return ary

    def to_repr(self):
        return "(" + self.to_lrepr() + ")"

    def to_lrepr(self):
        car = self.car.to_repr()
        cdr = self.cdr
        if cdr.is_nil(): #end of proper list
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
        if self.cdr.is_nil():
            return W_List(self.car, w_pair)
        else:
            return W_List(self.car, self.cdr.cons(w_pair))

    def comma(self, w_pair):
        if self.cdr.is_nil():
            self.cdr = w_pair
            return self
        else:
            self.cdr.comma(w_pair)
            return self

    def compile(self, runtime, env_stack, stack, operand_stack):
        return env_stack, stack, w_list([self.car, W_Call(self.cdr)]).comma(operand_stack)


@jit.unroll_safe
def w_list(args):
    w_l = W_List(args[0], w_nil)
    for w_item in args[1:]:
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

    def compile(self, runtime, env_stack, stack, operand_stack):
        return env_stack, W_List(self, stack), operand_stack

    def is_nil(self):
        return True

w_nil = W_Nil()


class W_PrimitiveCall(W_Object):
    def __init__(self, w_primitive):
        self.w_primitive = w_primitive

    def compile(self, runtime, env_stack, stack, operand_stack):
        operands_w = []
        for i in xrange(self.w_primitive.arg_count):
            assert isinstance(stack, W_List)
            operands_w.append(stack.car)
            stack = stack.cdr
        w_res = self.w_primitive.fun(operands_w)
        return env_stack, W_List(w_res, stack), operand_stack

    def to_repr(self):
        return "#<primitive %s>" % self.w_primitive.fun


class W_OperateCall(W_PrimitiveCall):
    def compile(self, runtime, env_stack, stack, operand_stack):
        op_env = stack.car
        stack = stack.cdr
        assert isinstance(stack, W_List)
        fexpr = stack.car
        stack = stack.cdr
        assert isinstance(stack, W_List)
        operands = stack.car
        stack = stack.cdr
        return W_List(op_env, env_stack), W_List(operands, stack), w_list([fexpr, W_Return()]).comma(operand_stack)

    def to_repr(self):
        return "#<operate>"


class W_EvalCall(W_PrimitiveCall):
    def compile(self, runtime, env_stack, stack, operand_stack):
        eval_env = stack.car
        stack = stack.cdr
        assert isinstance(stack, W_List)
        w_exp = stack.car
        stack = stack.cdr
        return W_List(eval_env, env_stack), stack, w_list([w_exp, W_Return()]).comma(operand_stack)

    def to_repr(self):
        return "#<eval>"


class W_Call(W_Object):
    def __init__(self, w_operands):
        self.w_operands = w_operands

    def to_repr(self):
        return "#<call>"

    def compile(self, runtime, env_stack, stack, operand_stack):
        fexpr = stack.car
        stack = stack.cdr
        assert isinstance(fexpr, W_Fexpr)
        return env_stack, W_List(self.w_operands, stack), W_List(fexpr, operand_stack)


class W_Return(W_Object):
    def compile(self, runtime, env_stack, stack, operand_stack):
        return env_stack.cdr, stack, operand_stack

    def to_repr(self):
        return "#<return>"


class W_Fexpr(W_Object):
    def __init__(self, env_param, params, static_env, body):
        self.env_param = env_param
        self.params = params
        self.static_env = static_env
        self.body = body

    def to_string(self):
        return '#<an fexpr>'

    to_repr = to_string

    def compile(self, runtime, env_stack, stack, operand_stack):
        w_operands = stack.car
        stack = stack.cdr

        local_names = W_List(self.env_param, self.params)
        local_values = W_List(env_stack.car, w_operands)
        local_env = W_List(runtime.bind(local_names, local_values), self.static_env)

        return W_List(local_env, env_stack), stack, w_list([self.body, W_Return()]).comma(operand_stack)


class W_BasePrimitive(W_Fexpr):
    CallClass = W_PrimitiveCall

    def __init__(self):
        self.arg_count = 0

    @jit.unroll_safe
    def compile(self, runtime, env_stack, stack, operand_stack):
        argcount = 0
        w_operands = stack.car
        stack = stack.cdr
        operand_stack = W_List(self.CallClass(self), operand_stack)
        while w_operands is not w_nil:
            assert isinstance(w_operands, W_List)
            operand_stack = W_List(w_operands.car, operand_stack)
            w_operands = w_operands.cdr
            argcount += 1
        if argcount < self.arg_count:
            raise QuoppaException("too few arguments to primitive")
        elif argcount > self.arg_count:
            raise QuoppaException("too many arguments to primitive")
        return env_stack, stack, operand_stack


class W_Primitive(W_BasePrimitive):
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
        self.arg_count = arg_count
        self.fun = namespace[fun.__name__]
        self.name = fun.__name__

    def to_string(self):
        return "#<primitive %s>" % self.name
    to_repr = to_string


class W_Vau(W_Primitive):
    def compile(self, runtime, env_stack, stack, operand_stack):
        w_operands = stack.car
        stack = stack.cdr
        return env_stack, W_List(self.fun([env_stack.car, w_operands]), stack), operand_stack

    def to_string(self):
        return "#<primitive vau>"
    to_repr = to_string


class W_Operate(W_BasePrimitive):
    CallClass = W_OperateCall

    def __init__(self):
        self.arg_count = 3

    def to_string(self):
        return "#<primitive operate>"
    to_repr = to_string    


class W_Eval(W_BasePrimitive):
    CallClass = W_EvalCall

    def __init__(self):
        self.arg_count = 2

    def to_string(self):
        return "#<primitive eval>"
    to_repr = to_string    
