from pypy.rlib.objectmodel import specialize

from execution_model import (W_List, symbol, w_nil, W_Symbol, QuoppaException,
                             W_Vau, W_Primitive, W_Fexpr, w_list)

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
            raise QuoppaException("can't bind %s %s" % (param, val))

    def lookup(self, name, env):
        if env is w_nil or not isinstance(env, W_List):
            raise QuoppaException("cannot find %s in %s" % (name, env))
        while env is not w_nil:
            frame = env.car
            while frame is not w_nil:
                pair = frame.car
                if not isinstance(pair, W_List):
                    raise QuoppaException("Consistency error! Non pair %s in frame" % pair)
                if pair.car.equal(name):
                    return pair
                frame = frame.cdr
                if not isinstance(frame, W_List):
                    raise QuoppaException("Consistency error! Non cons %s as frame cdr" % frame)
            env = env.cdr
            if not isinstance(env, W_List):
                    raise QuoppaException("Consistency error! Non cons %s as env cdr" % env)

    def m_eval(self, env, exp):
        if env is w_nil:
            env = self.global_env
        if isinstance(exp, W_Symbol):
            return self.lookup(exp, env).cdr.car
        elif exp is w_nil:
            return w_nil
        elif isinstance(exp, W_List):
            return self.operate(env, self.m_eval(env, exp.car), exp.cdr)
        else:
            return exp

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
