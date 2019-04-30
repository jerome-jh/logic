from copy import *
from itertools import *

""" Requires Python >= 3.5, syntax error otherwise """

__all__ = ['AND', 'OR', 'IMP', 'EQ', 'NOT', 'CNF', 'math_str', 'code_str', 'wolf_str', 'dimacs_str', 'is_cnf', 'count_variable', 'to_sat']

## TODO: check input for AND, OR, etc ... must be non zero integers

def AND(*arg):
    return ANDl(arg)

def ANDl(a):
    """ a is an iterable """
    return Exp(AND_op, a)

def OR(*arg):
    return ORl(arg)

def ORl(a):
    """ a is an iterable """
    return Exp(OR_op, a)

def IMP(a, b):
    return Exp(IMP_op, (a, b))

def EQ(a, b):
    return Exp(EQ_op, (a, b))

def NOT(a):
    return Exp(NOT_op, (a,))

def CNF(exp):
    if is_atom(exp):
        return exp
    exp = convert_eq(exp)
    exp = convert_imp(exp)
    exp = convert_not(exp)
    if is_atom(exp):
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
    prec = 0
    position = 'in'

class OR_op(OP):
    arity = -2
    symb = '\\/'
    wolf_symb = 'Or'
    func = OR
    prec = 1
    position = 'in'

class IMP_op(OP):
    arity = 2
    symb = '->'
    wolf_symb = 'Implies'
    func = IMP
    prec = 2
    position = 'in'

class EQ_op(OP):
    arity = 2
    symb = '='
    wolf_symb = 'Equivalent'
    func = EQ
    prec = 3
    position = 'in'

class NOT_op(OP):
    arity = 1
    symb = '-'
    wolf_symb = 'Not'
    func = NOT
    prec = -1
    position = 'pre'

""" Data type for an expression
    An expression is a double (operator, arguments)
    Arguments is typically a list
    The reason for this class is to make explicit the data structure underlying
    an expression. But also, since list() and tuple() do not support views in
    standard Python (contrary to Numpy), we cannot extract the arguments without
    performing a copy should the operator and the arguments be put in the same
    list or tuple.
"""
class Exp:
    __type_of_arg = list
    def __init__(self, op, arg):
        """ Create a composed (molecular) expression made of an operator and its operands
            arg is an iterable """
        self.__e = (op, Exp.__type_of_arg(arg))
        assert_arity(self.op(), self.arg())
    def op(self):
        """ Return the operator of the expression """
        return self.__e[0]
    def arg(self):
        """ Return the arguments of the expression """
        return self.__e[1]
    def decomp(self):
        return self.op(), self.arg()
    def __str__(self):
        return str(self.__type_of_arg(chain([self.op()], self.arg())))
    def __equal__(self, b):
        pass

def is_exp(exp):
    """ Return true if exp is an expression """
    return isinstance(exp, Exp)

def is_atom(exp):
    """ An atom is anything that is not an expression """
    return not is_exp(exp)

def tail_cbk_f(tail):
    """ Return a set of callbacks that build the path leading to node
        tail is an empty list
        Please not this is not purely functional since tail is modified "in place"
        """
    def prefix_cbk(exp):
        tail.append(exp)
    def infix_cbk(exp, pos):
        pass
    def postfix_cbk(exp):
        tail.pop()
    def atom_cbk(a):
        pass
    return (prefix_cbk, infix_cbk, postfix_cbk, atom_cbk)

def seq_f(functions):
    """ Call a number of functions in sequence """
    def seq(*arg):
        for f in functions:
            f(*arg)
    return seq

def seq_cbk(set1, set2):
    """ Combine two sets of callbacks, calling them in sequence """
    return tuple(map(seq_f, zip(set1, set2)))

def make_tail_cbk_f(cbk, tail):
    """ Combine the given callback with the tail callbacks
        tail is an empty list """
    tail_cbk = tail_cbk_f(tail)
    return (seq_f((cbk[0], tail_cbk[0])), cbk[1], seq_f((tail_cbk[2], cbk[2])), cbk[3])

def math_str(exp):
    """ Print exp in usual mathematical notation """
    tail = list()
    l = list()
    def prefix_cbk(exp):
        op = exp.op()
        if op.position == 'pre':
            l.append(op.symb)
        if len(tail) > 0:
            parent_op = tail[-1].op()
            if op.prec >= parent_op.prec:
                ## Current op has less precedence than parent, need for parentheses
                l.append('(')
        ## else: root node, no need for parentheses
    def infix_cbk(exp, pos):
        op = exp.op()
        if op.position == 'in':
            l.append(op.symb)
    def postfix_cbk(exp):
        op = exp.op()
        if op.position == 'post':
            l.append(op.symb)
        if len(tail) > 0:
            parent_op = tail[-1].op()
            if op.prec >= parent_op.prec:
                l.append(')')
        ## else: root node, no need for parentheses
    def atom_cbk(a):
        l.append(str(a))
    visit_dflr(exp, make_tail_cbk_f((prefix_cbk, infix_cbk, postfix_cbk, atom_cbk), tail))
    return ''.join(l)

def code_str(exp):
    """ Print exp as equivalent code using this module API """
    l = list()
    def prefix_cbk(exp):
        l.append(exp.op().func.__name__ + '(')
    def infix_cbk(exp, pos):
        l.append(',')
    def postfix_cbk(exp):
        l.append(')')
    def atom_cbk(a):
        l.append(str(a))
    visit_dflr(exp, (prefix_cbk, infix_cbk, postfix_cbk, atom_cbk))
    return ''.join(l)

def wolf_str(exp):
    """ Tentative output to the so called Wolfram "language"
        This is useful for checking validity of the output
        But the language itself is so picky and unpredictable that careful
        human inspection is required every time. """
    if is_exp(exp):
        op, arg = exp.decomp()
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

def count_variable_r(exp):
    s = set()
    if is_exp(exp):
        arg = exp.arg()
        for a in arg:
            if is_exp(a):
                s.update(count_variable_r(a))
            else:
                s.add(abs(a))
    else:
        ## Can only occur at root of the 'tree'
        s.add(abs(exp))
    return s

def count_variable(exp):
    s = count_variable_r(exp)
    return len(s)

def dimacs_str(exp):
    if not is_cnf(exp):
        Exception('Expression is not CNF, cannot convert to DIMACS')
    ## Count number of variables
    nv = count_variable(exp)
    if is_exp(exp):
        car, cdr = exp.decomp()
        if car.func == AND:
            nc = len(cdr)
            s = 'p cnf %d %d\n'%(nv,nc)
            for e in cdr:
                car, cdr2 = e.decomp()
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
    if is_exp(exp):
        car, cdr = exp.decomp()
        if car.func == AND:
            for i, e in enumerate(cdr):
                if is_exp(e):
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
        """ exp must be an Exp or an atom
            Visit the tree depth first, post-order (LRN)
        """
        if is_atom(exp):
            ## reached a leaf of tree
            return exp
        op, arg = exp.decomp()
        arg_int = list(map(visit_lrn_r, arg))
        op_out, arg_out = node_cbk(op, arg_int)
        ## TODO: op_out.func does a number of checks we may want to avoid
        return op_out.func(*arg_out)
    return visit_lrn_r

def visit_lrn(exp, node_cbk):
    """ exp must be an Exp or an atom
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
            if is_atom(exp):
                ## reached a leaf of tree
                exp_out = [exp]
            else:
                op, arg = exp.decomp()
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
    """ exp must be an Exp or an atom
        Visit the tree depth first, post-order (LRN), passing parent
        op to node callback
        The parent node may see its number of arguments change
        list.
    """
    return visit_lrn_p_f(node_cbk)(None)(exp)[0]

def visit_dflr(exp, cbk):
    """ exp is an Exp or an atom
        Visit the tree depth first, then left to right
        This is what is also called a left hand side visit
        A callback is called for nodes pre, in and post order
        For leaves yet another callback is called
        Nodes are of type Exp
        Leaves are atoms
    """
    def visit_dflr_r_f(cbk):
        pre_cbk, in_cbk, post_cbk, atom_cbk = cbk[0], cbk[1], cbk[2], cbk[3]
        def visit_dflr_r(exp):
            if is_atom(exp):
                atom_cbk(exp)
            else:
                pre_cbk(exp)
                op, arg = exp.decomp()
                visit_dflr_r(arg[0])
                for i in range(1, len(arg)):
                    in_cbk(exp, i)
                    visit_dflr_r(arg[i])
                post_cbk(exp)
        return visit_dflr_r
    visit_dflr_r_f(cbk)(exp)

def convert_eq(exp):
    """ exp must be a list of list """
    return visit_lrn(exp, convert_eq_node)

def convert_imp(exp):
    """ exp must be a list of list """
    return visit_lrn(exp, convert_imp_node)

def convert_not(exp):
    """ exp must be an Exp or an atom """
    if is_atom(exp):
        return exp
    op, arg = exp.decomp()
    if op.func == NOT:
        assert(len(arg) == 1)
        if is_exp(arg[0]):
            op2, arg2 = arg[0].decomp()
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
        return Exp(op, map(convert_not, arg))

def distribute_or_cbk(parent_op, parent_arg, current_op, current_arg):
    if parent_op.func == OR and current_op.func == AND:
        ## Distribute to the right
        arg_out = list()
        for ca in current_arg:
            ca.extend(parent_arg)
            arg_out.append(ca)
        return AND(list(map(OR, arg_out)))
    elif parent_op.func == AND and current_op.func == OR:
        ## Distribute to the left
        arg_out = list()
        ## TODO: check if not equivalent to above loop
        for pa in parent_arg:
            pa.extend(current_arg)
            arg_out.append(ca)
        return AND(list(map(OR, arg_out)))

def distribute_or_new(exp):
    return visit_lrn_pa(exp, distribute_or_cbk)

def distribute_or(exp):
    """ exp must be a list """
    if is_atom(exp):
        return exp
    op, arg = exp.decomp()
    if op.func == OR:
        for i, e in enumerate(arg):
            if is_exp(e):
                op, arg2 = e.decomp()
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
        return Exp(op, map(distribute_or, arg))

def associate(exp):
    """ exp must be a list of list
        Associate OR and AND in a single tree visit
    """
    return visit_lrn_p(exp, associate_cbk_f([OR, AND]))

def is_cnf(exp):
    if is_atom(exp):
        return True
    car, cdr = exp.decomp()
    if car.func == AND:
        for e in cdr:
            if is_exp(e):
                car, cdr2 = e.decomp()
                if car.func != OR:
                    return False
                for e2 in cdr2:
                    if is_exp(e2):
                        return False
        return True
    elif car.func == OR:
        for e in cdr:
            if is_exp(e):
                return False
        return True
    else:
        return False

if __name__ == '__main__':
    e = AND(1,OR(2,3))
    print(code_str(e))
    print(math_str(e))
    e = OR(1,AND(2,3))
    print(code_str(e))
    print(math_str(e))
    e = NOT(AND(2,3))
    print(code_str(e))
    print(math_str(e))
    e = AND(NOT(1),2)
    print(code_str(e))
    print(math_str(e))
    e = AND(1,OR(AND(2,3),4))
    print(code_str(e))
    print(math_str(e))
    quit()

    print(code_str(Exp(*e.decomp())))
    print(math_str(e))
    quit()

    e = AND(1,OR(2,3))
    print(e)
    print(code_str(e))
    print(CNF(e))
    print(code_str(CNF(e)))

    e = OR(1,AND(2,3))
    print(e)
    print(code_str(e))
    print(CNF(e))
    print(code_str(CNF(e)))

