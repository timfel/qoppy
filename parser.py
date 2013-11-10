from rpython.rlib.parsing.pypackrat import PackratParser
from rpython.rlib.parsing.makepackrat import BacktrackException, Status

from execution_model import (W_List, W_Integer, W_Real, W_String, w_nil,
                             symbol, w_true, w_false, QuoppaException)

def str_unquote(s):
    str_lst = []
    pos = 1
    last = len(s)-1
    while pos < last:
        ch = s[pos]
        if ch == '\\':
            pos += 1
            ch = s[pos]
            if ch == '\\' or ch == '\"':
                str_lst.append(ch)
            elif ch == 'n':
                str_lst.append("\n")
            else:
                raise QuoppaException(ch)
        else:
            str_lst.append(ch)

        pos += 1

    return ''.join(str_lst)

class QuoppaParser(PackratParser):
    r"""
    NIL:
        c = `nil`
        IGNORE*
        return {w_nil};

    STRING:
        c = `\"([^\\\"]|\\\"|\\\\|\\n)*\"`
        IGNORE*
        return {W_String(str_unquote(c))};

    CHARACTER:
        c = `#\\(.|[A-Za-z]+)`
        IGNORE*
        return {W_String(c[2:])};

    SYMBOL:
        c = `[\+\-\*\^\?a-zA-Z!<=>_~/$%&:][\+\-\*\^\?a-zA-Z0-9!<=>_~/$%&:.]*`
        IGNORE*
        return {symbol(c)};

    FIXNUM:
        c = `\-?(0|([1-9][0-9]*))`
        IGNORE*
        return {W_Integer(int(c))};

    FLOAT:
        c = `\-?([0-9]*\.[0-9]+|[0-9]+\.[0-9]*)`
        IGNORE*
        return {W_Real(float(c))};

    BOOLEAN:
        c = `#(t|f)`
        IGNORE*
        return {w_true if (c[1] == 't') else w_false};

    IGNORE:
        ` |\n|\t|;[^\n]*`;

    EOF:
        !__any__;

    file:
        IGNORE*
        s = sexpr*
        EOF
        return {s};

    quote:
       `'`
       s = sexpr
       return {quote(s)};

    qq:
       `\``
       s = sexpr
       return {qq(s)};


    unquote_splicing:
       `\,@`
       s = sexpr
       return {unquote_splicing(s)};

    unquote:
       `\,`
       s = sexpr
       return {unquote(s)};

    sexpr:
        list
      | quote
      | qq
      | unquote_splicing
      | unquote
      | NIL
      | FLOAT
      | FIXNUM
      | BOOLEAN
      | SYMBOL
      | CHARACTER
      | STRING;

    list:
        '('
        IGNORE*
        p = pair
        ')'
        IGNORE*
        return {p};

    pair:
        car = sexpr
        '.'
        IGNORE*
        cdr = sexpr
        return {W_List(car, cdr)}
      | car = sexpr
        cdr = pair
        return {W_List(car, cdr)}
      | return {w_nil};
    """

def parse(code):
    p = QuoppaParser(code)
    return p.file()

##
# Parser helpers
##
def quote(sexpr):
    return W_List(symbol('quote'), W_List(sexpr, w_nil))

def qq(sexpr):
    return W_List(symbol('quasiquote'), W_List(sexpr, w_nil))

def unquote(sexpr):
    return W_List(symbol('unquote'), W_List(sexpr, w_nil))

def unquote_splicing(sexpr):
    return W_List(symbol('unquote-splicing'), W_List(sexpr, w_nil))
