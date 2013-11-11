from rpython.rlib import jit
from rpython.rlib.objectmodel import we_are_translated

from execution_model import W_Object, W_List, w_nil, W_Symbol, QuoppaException


class VersionTag(object):
    pass


def frame_write_exception():
    raise QuoppaException("can only add '(symbol value) pairs to Frames")


class W_RootFrameEntry(W_List):
    def cons(self, w_pair):
        raise NotImplementedError()
    comma = cons

    def set_car_b(self, w_val):
        frame_write_exception()
    set_cdr_b = set_car_b

    def to_string(self):
        return "#<enventry: %s - %s>" % (self.car, self.cdr)
    to_repr = to_string


class W_FrameValue(W_RootFrameEntry):
    """A list that provides only a value in a frame"""
    def __init__(self, w_val, w_frame):
        self.w_val = w_val
        self.w_frame = w_frame
        self.car = w_val
        self.cdr = None

    def set_car_b(self, w_pair):
        self.car = w_pair


class W_FrameEntry(W_RootFrameEntry):
    def set_car_b(self, w_val):
        if not isinstance(w_val, W_Symbol):
            frame_write_exception()
        self.car = w_val

    def set_cdr_b(self, w_pair):
        if not isinstance(w_pair, W_List):
            frame_write_exception()
        self.cdr = w_pair

    def cons(self, w_pair):
        raise NotImplementedError()
    comma = cons


class W_Frame(W_RootFrameEntry):
    _immutable_fields_ = ["_dict", "_static_env"]

    def __init__(self, local_env, static_env):
        self._dict = {}
        self._static_env = static_env
        self._version = VersionTag()
        self._local_env = local_env
        self.car = w_nil
        self.cdr = None

    def set_car_b(self, w_pair):
        if not isinstance(w_pair, W_List):
            frame_write_exception()
        new_car = w_pair.car
        cdr = w_pair.cdr
        if self.car and not cdr == self.car:
            raise QuoppaException("set-car! for frame object must use the current car of frame as cdr")
        if not isinstance(cdr, W_List) or not isinstance(new_car, W_List):
            frame_write_exception()

        symbol = new_car.car
        value = new_car.cdr
        if not isinstance(symbol, W_Symbol) or not isinstance(value, W_List):
            frame_write_exception()
        self.car = new_car
        self.set(symbol, value.car)

    def set(self, param, val):
        assert isinstance(param, W_Symbol)
        entry = W_FrameEntry(param, W_FrameValue(val, self))
        self._dict[param.name] = entry
        if not self.car:
            self.car = entry
        self.mutate()

    def mutate(self):
        self._version = VersionTag()

    def get(self, param):
        assert isinstance(param, W_Symbol)
        return self._get_pure(param, self._version)

    @jit.elidable
    def _get_pure(self, param, version):
        w_res = self._dict.get(param.name, None)
        if not w_res and self._static_env:
            return self._static_env.get(param)
        else:
            return w_res

    def to_string(self):
        if we_are_translated():
            return "#<env>"
        else:
            return "#<env: %s>" % self._dict
    to_repr = to_string
