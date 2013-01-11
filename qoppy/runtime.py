from pypy.rlib.objectmodel import specialize

from execution_model import (W_List, symbol, w_nil, W_Symbol, QuoppaException,
                             W_Vau, W_Primitive, W_Fexpr, w_list,
                             W_Call, W_FexprCall, W_PrimitiveCall)


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


class Runtime(object):
    @specialize.memo()
    def __init__(self, primitives):
        vau = W_Vau(self.vau)
        global_frame = self.bind(symbol("vau"), vau)
        primitives["eval"] = self.m_eval
        primitives["operate"] = self.operate
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
                if pair.car.equal(name):
                    return pair
                frame = frame.cdr
            env = env.cdr
            if not isinstance(env, W_List):
                    raise QuoppaException("Consistency! Non cons %s as env cdr" % env.to_string())
        raise QuoppaException("cannot find %s in env" % name.to_string())

    def operate(self, env, fexpr, operands):
        return fexpr.call(self, env, operands)

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

    def m_eval(self, env, w_exp):
        if env is w_nil:
            env = self.global_env
        stack_w = []
        while True:
            if isinstance(w_exp, W_List) and not w_exp is w_nil:
                stack_w.append(W_Call(w_exp.cdr)) # stash arguments
                w_exp = w_exp.car
            elif (isinstance(w_exp, W_Fexpr) and stack_w and
                  isinstance(stack_w[-1], W_Call)):
                w_operands = stack_w.pop().w_operands
                w_exp = w_exp.call(self, env, w_operands)
            elif isinstance(w_exp, W_FexprCall):
                return self.m_eval(w_exp.env, w_exp.w_body) # new frame
            elif isinstance(w_exp, W_PrimitiveCall):
                operands_w = []
                w_operands = w_exp.w_operands
                while w_operands is not w_nil:
                    assert isinstance(w_operands, W_List)
                    operands_w.append(self.m_eval(w_exp.env, w_operands.car)) # new frame
                    w_operands = w_operands.cdr
                return w_exp.execute(operands_w)
            elif len(stack_w) > 0:
                if isinstance(w_exp, W_Symbol):
                    cdr = self.lookup(w_exp, env).cdr
                    assert isinstance(cdr, W_List) and cdr is not w_nil
                    w_exp = cdr.car
            elif isinstance(w_exp, W_Symbol):
                cdr = self.lookup(w_exp, env).cdr
                assert isinstance(cdr, W_List) and cdr is not w_nil
                return cdr.car
            else:
                return w_exp
