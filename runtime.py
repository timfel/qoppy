from execution_model import (W_List, symbol, w_nil, W_Symbol, QuoppaException,
                             W_Vau, W_Primitive, W_Fexpr)

class Runtime(object):
    def __init__(self, primitives):
        self.global_env = W_List(W_List(symbol("vau"), W_Vau(self.vau)), w_nil)
        primitives["eval"] = self.m_eval
        primitives["operate"] = self.operate
        primitives["lookup"] = self.lookup
        for name in primitives:
            prim = W_Primitive(primitives[name])
            self.global_env.comma(W_List(W_List(symbol(name), prim), w_nil))

    def bind(self, param, val):
        if param is w_nil and val is w_nil:
            return w_nil
        elif isinstance(param, W_Symbol):
            if param.name == "_":
                return w_nil
            else:
                return W_List(W_List(param, val), w_nil)
        elif isinstance(param, W_List) and isinstance(val, W_List):
            if param is w_nil:
                raise QuoppaException("too many arguments")
            elif val is w_nil:
                raise QuoppaException("too few arguments")
            return self.bind(param.car, val.car).comma(self.bind(param.cdr, val.cdr))
        else:
            raise QuoppaException("can't bind %s %s" % (param, val))

    def lookup(self, name, env):
        pair = env.car
        env = env.cdr
        while pair is not w_nil:
            assert isinstance(pair, W_List)
            if pair.car.equal(name):
                return pair
            if env is w_nil:
                break
            pair = env.car
            env = env.cdr
        raise QuoppaException("could not find %s" % name)

    def m_eval(self, env, exp):
        if env is w_nil:
            env = self.global_env
        if isinstance(exp, W_Symbol):
            return self.lookup(exp, env).cdr
        elif exp is w_nil:
            return w_nil
        elif isinstance(exp, W_List):
            return self.operate(env, self.m_eval(env, exp.car), exp.cdr)
        else:
            return exp

    def operate(self, env, fexpr, operands):
        return fexpr.call(self, env, operands)

    def vau(self, static_env, vau_operands):
        params = vau_operands.car
        env_param = vau_operands.cdr.car
        body = vau_operands.cdr.cdr.car
        return W_Fexpr(env_param, params, static_env, body)
