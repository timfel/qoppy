from rpython.rlib import jit
from rpython.rlib.objectmodel import specialize

from execution_model import (W_List, symbol, w_nil, W_Symbol, QuoppaException,
                             W_Vau, W_Primitive, W_Fexpr, w_list)
from frame import W_Frame


def get_printable_location(self, exp):
    return exp.to_string()


class Runtime(object):
    jitdriver = jit.JitDriver(
        greens=['self', 'fexpr'],
        reds=['operands', 'env'],
        get_printable_location=get_printable_location
    )

    @specialize.memo()
    def __init__(self, primitives):
        vau = W_Vau(self.vau)

        global_env = self.bind(symbol("vau"), vau)
        global_frame = W_Frame(w_list(global_env), None)
        global_frame.set(symbol("vau"), vau)

        primitives["eval"] = self.m_eval
        primitives["operate"] = self.operate
        primitives["lookup"] = self.lookup
        for name in primitives:
            prim = W_Primitive(primitives[name])
            global_env.comma(w_list(w_list(symbol(name), prim)))
            global_frame.set(symbol(name), prim)

        # XXX
        global_frame.car = global_env.car
        global_frame.cdr = global_env.cdr

        self.global_env = global_frame

    def bind(self, param, val):
        if param is w_nil and val is w_nil:
            return w_nil
        elif isinstance(param, W_Symbol):
            if param.name == "_":
                return w_nil
            else:
                # For debugging
                if isinstance(val, W_Fexpr) and not val.name:
                    val.name = param.name
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
        w_res = None
        if isinstance(env, W_Frame):
            w_res = env.get(name)
        else:
            w_res = self._slow_lookup(name, env)
        if not w_res:
            raise QuoppaException("cannot find %s in env" % name.to_string())
        return w_res

    def _slow_lookup(self, name, env):
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

    @specialize.argtype(2)
    def m_eval(self, env, exp):
        if env is w_nil:
            env = self.global_env
        if isinstance(exp, W_Symbol):
            cdr = self.lookup(exp, env).cdr
            assert isinstance(cdr, W_List) and cdr is not w_nil
            return cdr.car
        elif exp is w_nil:
            return w_nil
        elif isinstance(exp, W_List):
            return self.operate(env, self.m_eval(env, exp.car), exp.cdr)
        else:
            return exp

    def operate(self, env, fexpr, operands):
        self.jitdriver.jit_merge_point(env=env, fexpr=fexpr, self=self, operands=operands)
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

    def create_frame(self, local_names, local_values, static_env=None, local_env=None, frame=None):
        if not frame:
            frame = W_Frame(local_env, static_env)

        if local_names is w_nil and local_values is w_nil:
            return frame
        elif isinstance(local_names, W_Symbol):
            if local_names.name != "_":
                # For debugging
                if isinstance(local_values, W_Fexpr) and not local_values.name:
                    local_values.name = local_names.name
                frame.set(local_names, local_values)
            return frame
        elif local_names is w_nil:
            raise QuoppaException("too many arguments")
        elif local_values is w_nil:
            raise QuoppaException("too few arguments")
        elif isinstance(local_names, W_List) and isinstance(local_values, W_List):
            frame = self.create_frame(local_names.car, local_values.car, frame=frame)
            return self.create_frame(local_names.cdr, local_values.cdr, frame=frame)
        else:
            raise QuoppaException("can't bind %s %s" % (local_names.to_string(), local_values.to_string()))
