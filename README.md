# Logic

This is a small Python package for doing symbolic boolean logic in Python. The main purpose is to calculate Conjunctive Normal Forms (CNF) of boolean equations within programs, when this is too difficult to do them offline with "pencil and paper" or when the number of variables is only known at runtime.

As such this is an API and there no syntactic sugar such as operator overloading. There is nothing for reading equations from an input file.

Still equations are fairly easy to enter and read in code and they can be outputted in various string formats, including:
- standard mathematical notation
- Wolframalpha language
- Python code using this API
- DIMACS

They can also be converted into a "list of list" suitable for calling a SAT solver, such as Pycosat.

Python >= 3.5 is required.

# API

Boolean operators AND, OR, IMP(plication), EQ(quivalence) and NOT are supported. AND and OR have unlimited arity. Variable are non zero integers. NOT can be noted - (minus sign).

# Limitations

The conversion to CNF does exactly what the math book says to do :)
The only simplication being done is the double negation, but that is part of the transformation to CNF.
No other simplification is done even the most obvious ones, so sometimes the output is unecessarily complicated.

# Example

```python
from logic import *

if __name__ == '__main__':
    s = EQ(2,3)
    c = AND(OR(-2,3),OR(-3,2))
    assert(is_cnf(c))
    assert(CNF(s) == c)
    e = EQ(s,c)
    ## e is a tautology, but since there is no simplification being done
    ## it results in a fairly long equation ;)
    print(math_str(CNF(e)))
```

