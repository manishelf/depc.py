from literals import *

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
        if(len(x) == len(y)):
            result = [AND(p, q) for p, q in zip(x, y)] # wtf is this syntax
            result.reverse
            return result
        else:
            print("x", x)
            print("y", y)
            raise NotImplementedError

    if bitwise:
        return x & y
    else: 
        return int (x and y)

def OR(x, y):

           
    if (type(x) == type([]) or type(y) == type([])) :
        x = pad_sequence(x, y)
        y = pad_sequence(y, x)  
        result = []
        if(len(x) == len(y)):
            # this will give binary addition 
            carry = 0
            while(len(x) > 0 and len(y) > 0):
                p = x.pop()
                q = y.pop()
                xor_pq = OR(AND(p, NOT(q)), AND(NOT(p), q))
                s0 = OR(AND(xor_pq, NOT(carry)), AND(NOT(xor_pq), carry))
                result.append(s0)
                carry = OR(AND(p, q), AND(carry, xor_pq))
            # result.append(carry) # ignore carry in result for now as it adds one addtional bit
            result.reverse()
            return result
        else:
            print("x", x)
            print("y", y)
            raise NotImplementedError

    if bitwise:
        return x | y # binary addition
    else: 
        return int (x or y)

def NAND(x, y):
    return NOT(AND(x, y))

def NOR(x, y):
    return NOT(OR(x, y))

def XOR(x, y):
    return OR(AND(x, NOT(y)), AND(NOT(x), y))

def XNOR(x, y):
    return NOT(XOR(x, y))
    # return OR(AND(NOT(x), NOT(y)), AND(x, y)) 


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

if __name__ == "__main__":
    x = [[1, 0]]
    y = [[0, 1]]
    print(OR(x, y))
