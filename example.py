from logic import *
import pycosat

if __name__ == '__main__':
    s = EQ(1,2)
    c = AND(OR(-1,2),OR(-2,1))
    assert(is_cnf(c))
    assert(CNF(s) == c)
    print(*pycosat.itersolve(to_sat(c)))
    e = EQ(s,c)
    ## e is a tautology, but since there is no simplification being done
    ## it results in a fairly long equation ;)
    print(math_str(CNF(e)))
