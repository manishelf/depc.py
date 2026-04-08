from literals import *

def TRUTHY(x) -> bool:
    if type(x) == type(True): 
        return x
    elif type(x) == type(1):
        return x != 0 
    elif type(x) == type([]):
        res = False
        for i in x:
            if TRUTHY(i):
                res = True
                return res
        return res
    else:
        print(x)
        raise NotImplementedErrorm

def NOT(x):
    if type(x) == type([]):
        result = [NOT(p) for p in x]
        return result
    if bitwise:
        return ~x 
    else: 
        return int (not x) 

def AND(x, y):
    
    if (type(x) == type([]) or type(y) == type([])) :
        x = pad_sequence(x, y)
        y = pad_sequence(y, x)  

        result = []
        result = [AND(p, q) for p, q in zip(x, y)] # wtf is this syntax
        result.reverse()
        return result

    if bitwise:
        return x & y
    else: 
        return int (x and y)

def OR(x, y):
    if (type(x) == type([]) or type(y) == type([])) :
        x = pad_sequence(x, y)
        y = pad_sequence(y, x)
        result = []
        
        # TODO:the examples should changed to handle this
        if True or not bitwise:
            carry = 0
            
            MAINTAIN_STRIDE = False; 
            # process from right LSB (BIG_ENDIAN)
            for p, q in zip(reversed(x), reversed(y)):
                if ((type(p) == type([]) or type(q) == type([])) and not MAINTAIN_STRIDE) :
                    # recurse into nested lists
                    result.append(OR(p, q))
                else:
                    # full adder at bit level
                    sum_bit = XOR(XOR(p,q), carry)
                    carry = OR(AND(p,q),AND(carry,XOR(p,q)))
                    result.append(sum_bit)
                    
            #if TRUTHY(carry):
            #    result.append(carry)
                
            result.reverse()

        else:
            result = [OR(p, q) for p, q in zip(x, y)]

        return result
        
    if bitwise:
        return x | y
    else:
        return int(x or y)

def NAND(x, y):
    return NOT(AND(x, y))

def NOR(x, y):
    return NOT(OR(x, y))

def XOR(x, y):
    return OR(AND(x, NOT(y)), AND(NOT(x), y))

def XNOR(x, y):
    return NOT(XOR(x, y))

if __name__ == "__main__":
    x = [[[1, 0],[1, 1]]]
    y = [[[1, 0],[1, 1]]]
    print(OR(x, y))
