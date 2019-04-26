from copy import *
from itertools import *

""" Requires Python >= 3.5, syntax error otherwise """

__all__ = ['AND', 'OR', 'IMP', 'EQ', 'NOT', 'CNF', 'math_str', 'code_str', 'wolf_str', 'dimacs_str', 'is_cnf', 'count_variable', 'to_sat']

## TODO: check input for AND, OR, etc ... must be non zero integers

def AND(*arg):
    return ANDl(arg)

def ANDl(a):
    """ a is an iterable """
    a = list(a)
    assert_arity(AND_op, a)
    return list(chain([AND_op], a))

def OR(*arg):
    return ORl(arg)

def ORl(a):
    """ a is an iterable """
    a = list(a)
    assert_arity(OR_op, a)
    return list(chain([OR_op], a))

def IMP(a, b):
    return [IMP_op, a, b]

def EQ(a, b):
    return [EQ_op, a, b]

def NOT(a):
    return [NOT_op, a]

def CNF(exp):
    if not islist(exp):
        return exp
    exp = convert_eq(exp)
    exp = convert_imp(exp)
    exp = convert_not(exp)
    if not islist(exp):
        return exp
    while not is_cnf(exp):
        #print('in:', code_str(exp))
        exp = associate(exp)
        #print(code_str(exp))
        exp = distribute_or(exp)
        #print('out:', code_str(exp))
    return exp

class OP:
    pass

class AND_op(OP):
    arity = -2
    symb = '/\\'
    wolf_symb = 'And'
    func = AND
    def assoc(e, *arg):
        e.extend(arg)

class OR_op(OP):
    arity = -2
    symb = '\\/'
    wolf_symb = 'Or'
    func = OR
    def assoc(self, *args):
        self.arg.extend(args)

class IMP_op(OP):
    arity = 2
    symb = '->'
    wolf_symb = 'Implies'
    func = IMP

class EQ_op(OP):
    arity = 2
    symb = '='
    wolf_symb = 'Equivalent'
    func = EQ

class NOT_op(OP):
    arity = 1
    symb = '-'
    wolf_symb = 'Not'
    func = NOT

def math_str(exp):
    """ Print exp in usual mathematical notation """
    if islist(exp):
        op, arg = lisp(exp)
        if op.arity == 2:
            return '(' + math_str(arg[0]) + ' ' + op.symb + ' ' + math_str(arg[1]) + ')'
        elif op.arity == 1:
            return op.symb + math_str(arg[0])
        elif op.arity == -2:
            s = '(' + math_str(arg[0])
            for e in arg[1:]:
                s += ' ' + op.symb + ' ' + math_str(e)
            s += ')'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        return str(exp)

def code_str(exp):
    """ Print exp as equivalent code using this module API """
    if islist(exp):
        op, arg = lisp(exp)
        if op.arity == 2:
            return op.func.__name__ + '(' + code_str(arg[0]) + ',' + code_str(arg[1]) + ')'
        elif op.arity == 1:
            return op.func.__name__ + '(' + code_str(arg[0]) + ')'
        elif op.arity == -2:
            s = op.func.__name__ + '(' + code_str(arg[0])
            for e in arg[1:]:
                s += ',' + code_str(e)
            s += ')'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        return str(exp)

def wolf_str(exp):
    """ Tentative output to the so called Wolfram "language"
        This is useful for checking validity of the output
        But the language itself is so picky and unpredictable that careful
        human inspection is required every time. """
    if islist(exp):
        op, arg = lisp(exp)
        if op.arity == 2:
            return op.wolf_symb + '[' + wolf_str(arg[0]) + ',' + wolf_str(arg[1]) + ']'
        elif op.arity == 1:
            return op.wolf_symb + '[' + wolf_str(arg[0]) + ']'
        elif op.arity == -2:
            s = op.wolf_symb + '[' + wolf_str(arg[0])
            for e in arg[1:]:
                s += ',' + wolf_str(e)
            s += ']'
            return s
        else:
            raise Exception('Unexpected arity')
    else:
        if (exp < 0):
            return wolf_str(NOT(-exp))
        else:
            return chr(ord('a') + exp - 1)
            #return 'Symbol["x%d"]'%(exp)

def __count_variable(exp):
    s = set()
    if islist(exp):
        for i in range(1,len(exp)):
            if islist(exp[i]):
                s.update(__count_variable(exp[i]))
            else:
                if exp[i] < 0:
                    s.add(-exp[i])
                else:
                    s.add(exp[i])
    else:
        ## Can only occur at root of the tree
        if exp < 0:
            s.add(-exp)
        else:
            s.add(exp)
    return s

def count_variable(exp):
    s = __count_variable(exp)
    return len(s)

def dimacs_str(exp):
    if not is_cnf(exp):
        Exception('Expression is not CNF, cannot convert to DIMACS')
    ## Count number of variables
    nv = count_variable(exp)
    if islist(exp):
        car, cdr = lisp(exp)
        if car.func == AND:
            nc = len(cdr)
            s = 'p cnf %d %d\n'%(nv,nc)
            for e in cdr:
                car, cdr2 = lisp(e)
                for e2 in cdr2:
                    s += '%s '%e2
                s+= '0\n'
            return s
        elif car.func == OR:
            ## only one clause
            nc = 1
            s = 'p cnf %d 1\n'%nv
            for e in cdr:
                s += '%s '%e
            s += '0\n'
            return s
    else:
        ## Ultra degenerated case
        return 'p cnf 1 1\n%d 0\n'%exp

def to_sat(exp):
    """ Return a list of list, suitable for e.g. Pycosat input """
    if not is_cnf(exp):
        Exception('Expression is not CNF, cannot convert to sat')
    if islist(exp):
        car, cdr = lisp(exp)
        if car.func == AND:
            for i, e in enumerate(cdr):
                if islist(e):
                    cdr[i] = e[1:]
                else:
                    cdr[i] = [e]
            return cdr
        elif car.func == OR:
            ## only one clause
            return [cdr]
    else:
        ## Can only occur at root of the tree
        return [[exp]]

def islist(exp):
    ## Numpy integers have __getitem__, so better check on __iter__
    return '__iter__' in dir(exp) and issubclass(exp[0], OP)

def lisp(exp):
    """ This is suboptimal because Python does not support views on lists,
        so taking a slice actually creates a copy """
    return exp[0], exp[1:]

def assert_arity(op, arg):
    if op.arity < 0:
        assert(len(arg) >= -op.arity)
    else:
        assert(len(arg) == op.arity)

def convert_eq_node(op, arg):
    if op.func == EQ:
        a = arg[0]
        b = arg[1]
        return AND_op, [IMP(a, b), IMP(copy(b), copy(a))]
    return op, arg

def convert_imp_node(op, arg):
    if op.func == IMP:
        a = arg[0]
        b = arg[1]
        return OR_op, [NOT(a), b]
    return op, arg

def visit_lrn_f(node_cbk):
    def visit_lrn_r(exp):
        """ exp must be a list of list
            Visit the tree depth first, post-order (LRN)
        """
        if not islist(exp):
            ## reached a leaf of tree
            return exp
        op, arg = lisp(exp)
        arg_int = list(map(visit_lrn_r, arg))
        op_out, arg_out = node_cbk(op, arg_int)
        ## TODO: op_out.func does a number of checks we may want to avoid
        return op_out.func(*arg_out)
    return visit_lrn_r

def visit_lrn(exp, node_cbk):
    """ exp must be a list of list
        Visit the tree depth first, post-order (LRN)
        The node_cbk function takes a list of arguments as argument
        and returns a complete expression, so the parent node of a
        transformed node does not see its number of arguments changing.
    """
    return visit_lrn_f(node_cbk)(exp)

def associate_cbk_f(op_func_list):
    def associate_cbk(parent_op, current_op, arg):
        if parent_op.func in op_func_list and parent_op.func == current_op.func:
            ## Merge parent_op arguments with current_op ones
            return arg
        else:
            ## No changes, just copy exp
            return [current_op.func(*arg)]
    return associate_cbk

def visit_lrn_p_f(node_cbk):
    def extend_f(l1):
        def f(l2):
            l1.extend(l2)
        return f
    def visit_lrn_p_r_f(parent_op) :
        def visit_lrn_p_r(exp):
            """ exp must be a list of list
                Visit the tree depth first, post-order (LRN)
                parent_op is None at root of tree
                Results are expanded into the parent's argument list
                so the parent operator may see its number of arguments
                change.
            """
            #print("visit_lrn_p_r in", exp)
            if not islist(exp):
                ## reached a leaf of tree
                exp_out = [exp]
            else:
                op, arg = lisp(exp)
                arg_int = list()
                ## TODO: maybe there is a more elegant way of "expanding" lists into result arg_int
                list(map(extend_f(arg_int), (list(map(visit_lrn_p_r_f(op), arg)))))
                if parent_op != None:
                    exp_out = node_cbk(parent_op, op, arg_int)
                else:
                    ## Root node, do not call node callback
                    exp_out = [op.func(*arg_int)]
            #print("visit_lrn_p_r out", exp_out)
            return exp_out
        return visit_lrn_p_r
    return visit_lrn_p_r_f

def visit_lrn_p(exp, node_cbk):
    """ exp must be a list of list
        Visit the tree depth first, post-order (LRN), passing parent
        op to node callback
        The parent node may see its number of arguments change
        list.
    """
    return visit_lrn_p_f(node_cbk)(None)(exp)[0]

def visit_nlr(exp, op_func, node_cbk):
    """ exp must be a list of list
        Visit the tree depth first, pre-order (NLR)
    """
    op, arg = lisp(exp)
    if op.func == op_func:
        assert_arity(op, arg)
        exp = node_cbk(arg)
    op, arg = lisp(exp)
    for i, a in enumerate(arg):
        if islist(a):
            arg[i] = visit_nlr(a, op_func, node_cbk)
    return list(chain([op], arg))

def convert_eq(exp):
    """ exp must be a list of list """
    return visit_lrn(exp, convert_eq_node)

def convert_imp(exp):
    """ exp must be a list of list """
    return visit_lrn(exp, convert_imp_node)

def convert_not(exp):
    """ exp must be a list """
    op, arg = lisp(exp)
    if op.func == NOT:
        assert(len(arg) == 1)
        if islist(arg[0]):
            op2, arg2 = lisp(arg[0])
            if op2.func == NOT:
                ## Simplify NOT NOT
                return arg2[0]
            elif op2.func == AND:
                return ORl(map(convert_not, list(map(NOT, arg2))))
            elif op2.func == OR:
                return ANDl(map(convert_not, list(map(NOT, arg2))))
            else:
                raise Exception("Operator '%s' should have been simplified by now"%op2.symb)
        else:
            ## Evaluate NOT
            return -arg[0]
    else:
        for i, a in enumerate(arg):
            if islist(a):
                exp[i+1] = convert_not(a)
        return exp

def distribute_or(exp):
    """ exp must be a list """
    op, arg = lisp(exp)
    if op.func == OR:
        for i, e in enumerate(arg):
            if islist(e):
                op, arg2 = lisp(e)
                if op.func == AND:
                    if i == 0:
                        ## distribute to the left
                        ai = arg2
                        o = arg[1]
                        of = lambda x: OR(x,o)
                        oi = arg[2:]
                        if not len(oi):
                            return ANDl(map(distribute_or, list(map(of, ai))))
                        else:
                            reta = ANDl(map(of, ai))
                            reto = OR(reta, *oi)
                            return distribute_or(reto)
                    else:
                        ## distribute to the right
                        o = arg[0:i]
                        ai = arg2
                        of = lambda x: ORl(list(chain(o,[x])))
                        oi = arg[i+1:]
                        if not len(oi):
                            return ANDl(map(distribute_or, list(map(of, ai))))
                        else:
                            reta = ANDl(map(of, ai))
                            reto = OR(reta, *oi)
                            return distribute_or(reto)
        return exp
    else:
        for i, e in enumerate(arg):
            if islist(e):
                exp[i+1] = distribute_or(e)
        return exp

def associate(exp):
    """ exp must be a list of list
        Associate OR and AND in a single tree visit
    """
    return visit_lrn_p(exp, associate_cbk_f([OR, AND]))

def is_cnf(exp):
    if not islist(exp):
        return True
    car, cdr = lisp(exp)
    if car.func == AND:
        for e in cdr:
            if islist(e):
                car, cdr2 = lisp(e)
                if car.func != OR:
                    return False
                for e2 in cdr2:
                    if islist(e2):
                        return False
        return True
    elif car.func == OR:
        for e in cdr:
            if islist(e):
                return False
        return True
    else:
        return False

