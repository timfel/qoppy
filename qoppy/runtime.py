from pypy.rlib import jit
from pypy.rlib.objectmodel import specialize

from parser import parse
from execution_model import (W_List, symbol, w_nil, W_Symbol, QuoppaException,
                             W_Vau, W_Operate, W_Eval, W_Primitive, W_Fexpr, w_list)


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

def get_printable_location(self, w_exp):
    # stack = []
    # for i in stack_w:
    #     stack += ("stack is %s" % i.to_string())
    #     stack += "\n"
    return w_exp.to_string()


class Runtime(object):
    jitdriver = jit.JitDriver(
        greens=["self", "w_exp"],
        reds=["env_stack", "stack", "operand_stack"],
        get_printable_location=get_printable_location,
    )

    @specialize.memo()
    def __init__(self, primitives):
        vau = W_Vau(self.vau)
        global_frame = self.bind(symbol("vau"), vau)
        global_frame.comma(w_list(w_list(symbol("operate"), W_Operate())))
        global_frame.comma(w_list(w_list(symbol("eval"), W_Eval())))

        primitives["lookup"] = self.lookup
        for name in primitives:
            prim = W_Primitive(primitives[name])
            global_frame.comma(w_list(w_list(symbol(name), prim)))
        self.global_env = w_list(global_frame)

    def bind(self, param, val):
        if param is w_nil and val is w_nil:
            return w_nil
        elif isinstance(param, W_Symbol):
            if param.name == "_":
                return w_nil
            else:
                return w_list(w_list(param, val))
        elif param is w_nil:
            raise QuoppaException("too many arguments")
        elif val is w_nil:
            raise QuoppaException("too few arguments")
        elif isinstance(param, W_List) and isinstance(val, W_List):
            return self.bind(param.car, val.car).comma(self.bind(param.cdr, val.cdr))
        else:
            raise QuoppaException("can't bind %s %s" % (param.to_string(), val.to_string()))

    # TODO: Probably wrong, look into this
    @jit.unroll_safe
    def lookup(self, name, env):
        if env is w_nil or not isinstance(env, W_List):
            raise QuoppaException("cannot find %s in %s" % (name.to_string(), env.to_string()))
        while env is not w_nil:
            frame = env.car
            while frame is not w_nil:
                if not isinstance(frame, W_List):
                    raise QuoppaException("Consistency! Non pair %s as frame" % frame.to_string())
                pair = frame.car
                if not isinstance(pair, W_List):
                    raise QuoppaException("Consistency! Non pair %s in frame" % pair.to_string())
                if not isinstance(pair.car, W_Symbol):
                    raise QuoppaException("Consistency! Non symbol %s in pair" % pair.to_string())
                if pair.car.equal(name):
                    return pair
                frame = frame.cdr
            env = env.cdr
            if not isinstance(env, W_List):
                raise QuoppaException("Consistency! Non cons %s as env cdr" % env.to_string())
        raise QuoppaException("cannot find %s in env" % name.to_string())

    def vau(self, static_env, vau_operands):
        assert isinstance(vau_operands, W_List)
        params = vau_operands.car

        env_cdr = vau_operands.cdr
        assert isinstance(env_cdr, W_List)
        env_param = env_cdr.car

        body_cdr = env_cdr.cdr
        assert isinstance(body_cdr, W_List)
        body = body_cdr.car

        return W_Fexpr(env_param, params, static_env, body)

    def interpret(self, env, w_exp):
        stack = w_nil
        operand_stack = w_list(w_exp)
        env_stack = w_list(env if env is not w_nil else self.global_env)
        while operand_stack is not w_nil:
            w_exp = operand_stack.car
            if isinstance(w_exp, W_Fexpr):
                self.jitdriver.can_enter_jit(
                    self=self, w_exp=w_exp,
                    env_stack=env_stack, stack=stack,
                    operand_stack=operand_stack
                )
            self.jitdriver.jit_merge_point(
                self=self, w_exp=w_exp,
                env_stack=env_stack, stack=stack,
                operand_stack=operand_stack
            )
            env_stack, stack, operand_stack = w_exp.compile(self, env_stack, stack, operand_stack.cdr)
            assert isinstance(env_stack, W_List)
            assert isinstance(stack, W_List)
            assert isinstance(operand_stack, W_List)
        return stack.car

    def execute(self, code):
        t = parse(code)
        w_res = None
        for s in t:
            w_res = self.interpret(w_nil, s)
        return w_res
