from qoppy.runtime import get_runtime
from qoppy.execution_model import *

class TestQoppa(object):
    def setup_method(self, obj):
        self.r = get_runtime()

    def test_primitives(self):
        w_res = self.r.execute("1")
        assert isinstance(w_res, W_Integer)
    
        w_res = self.r.execute("nil")
        assert w_res is w_nil
    
        w_res = self.r.execute('"foo"')
        assert isinstance(w_res, W_String)
    
        w_res = self.r.execute("1.1")
        assert isinstance(w_res, W_Real)

    def test_eval(self):
        w_res = self.r.execute("(eval nil 1)")
        assert isinstance(w_res, W_Integer)
    
        # if-like
        w_res = self.r.execute("""
        ((vau (n) env
          ((vau (b t f) env
                (eval env (bool (eval env b) t f)))
    
            (<= 1 n)
            1
            2))
          5)
        """)
        assert isinstance(w_res, W_Integer)
        assert w_res.intval == 1

    def test_defined_if(self):
        w_res = self.r.execute("""
        ((vau (name-of-define null) env
            (set-car! env (cons
                (cons name-of-define
                    (cons (vau (name exp) defn-env
                            (set-car! defn-env (cons
                                (cons name (cons (eval defn-env exp) null))
                                (car defn-env))))
                        null))
                (car env))))
            define ())
        
        (define if (vau (b t f) env
            (eval env (bool (eval env b) t f))))
    
        (if (<= 1 2) 10 20)
        """)
        assert w_res.intval == 10

    def test_defined_list(self):
        w_res = self.r.execute("""
        ((vau (name-of-define null) env
            (set-car! env (cons
                (cons name-of-define
                    (cons (vau (name exp) defn-env
                            (set-car! defn-env (cons
                                (cons name (cons (eval defn-env exp) null))
                                (car defn-env))))
                        null))
                (car env))))
            define ())
    
        (define if (vau (b t f) env
            (eval env (bool (eval env b) t f))))
        
        (define list (vau xs env
            (if (null? xs)
                '()
                (cons
                    (eval env (car xs))
                    (eval env (cons list (cdr xs)))))))
        (list 1 2 3 4)
        """)
        assert isinstance(w_res, W_List)
        assert w_res.to_array() == [1, 2, 3, 4]

    def test_defined_wrap(self):
        w_res = self.r.execute("""
        ((vau (name-of-define null) env
            (set-car! env (cons
                (cons name-of-define
                    (cons (vau (name exp) defn-env
                            (set-car! defn-env (cons
                                (cons name (cons (eval defn-env exp) null))
                                (car defn-env))))
                        null))
                (car env))))
            define ())
    
        (define wrap (vau (operative) oper-env
            (vau args args-env
                (operate args-env
                    (eval    oper-env operative)
                    (operate args-env list args)))))
    
        ((wrap (vau (n) n))
         (+ 1 2))
        """)
        assert w_res.intval == 3
