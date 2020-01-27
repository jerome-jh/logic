###
## Solving well known puzzle:
##
## Which answer is correct?
## 1. All of the below
## 2. None of the below
## 3. All of the above
## 4. At least one of the above
## 5. None of the above
## 6. None of the above
##
from logic import *
import pycosat

if __name__ == '__main__':
    e1 = EQ(1, AND(2,3,4,5,6))
    e2 = EQ(2, NOT(OR(3,4,5,6)))
    e3 = EQ(3, AND(1,2))
    e4 = EQ(4, OR(1,2,3))
    e5 = EQ(5, NOT(OR(1,2,3,4)))
    e6 = EQ(6, NOT(OR(1,2,3,4,5)))

    e = AND(e1, e2, e3, e4, e5, e6)
    s = list(pycosat.itersolve(to_sat(CNF(e))))
    ## Lucky enough to have only one solution?
    assert(len(s) == 1)
    print(s[0])
