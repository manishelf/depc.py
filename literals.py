ONE = 1
ZERO = 0
SEQUENCE_BASE = 2
bitwise = False


def pad_sequence(target, match):
    
    if(type(target) != type([])):
        target = [target]

    if(type(match) != type([])):
        match = [match]
    
    larger_len = max(len(target), len(match))
    
    target = target.copy()

    target.reverse()
    while len(target) < larger_len:
        target.append(0)
    target.reverse()
    
    return target

def sequence_to_decimal(seq, base):
    res = 0
    units = 1
    inp = seq.copy()
    inp.reverse()
    for i in range(len(inp)):
        res += inp[i]*(base**i)*units
    units *= 10
    return res

def sequence_to_hex(seq, base):
    res = ""
    inp = seq.copy()
    inp.reverse()

    while len(inp) % 4 != 0:
        inp.append(0)

    for i in range(0, len(inp), 4): # 0 4 8 16
        units_decimal = (
            inp[i]   * 1 +
            inp[i+1] * 2 +
            inp[i+2] * 4 +
            inp[i+3] * 8 
        )

        # Convert to hex
        if units_decimal < 10:
            res += str(units_decimal)
        else:
            res += chr(ord('A') + units_decimal - 10)

    res += "X0"
    return res[::-1]

def decimal_to_sequence(num, base):
    if(num == 0):
        return [0]

    res = []
    units = 1
    while num > 0:
        rem = num % base
        num = num // base
        res.append(rem)
        units *= 10
    res.reverse()
    return res

def decimal_to_hex(num):
    seq = decimal_to_sequence(num, SEQUENCE_BASE)
    return sequence_to_hex(seq, SEQUENCE_BASE) 

def is_hex(num):
    res = False
    num = num.upper()
    if(type(num) == type("") and len(num) > 0):
        if(num.startswith("0X")):
            for char in num[2:]:
                if char.isdigit() or "A" <= char <= "F": # cool syntax
                    res = True
                    return res
    return res

def hex_to_sequence(num, base):
    res = []
    inp = (num[2:].upper())[::-1]
    for char in inp:
        dec = 0
        if(char.isdigit()):
            dec = int(char)
        elif 'A' <= char <= 'F':
            dec = (ord(char) - 65 + 10)
        else:
            raise ValueError("cannot parse as hex", num)
        seq = decimal_to_sequence(dec, base)
        seq.reverse()
        while len(seq) % 4 != 0:
            seq.append(0)
        res.extend(seq)
    
    res.reverse()
    return res

def hex_to_decimal(num):
    seq = hex_to_sequence(num, SEQUENCE_BASE)
    return sequence_to_decimal(seq, SEQUENCE_BASE)

def main(num1):
    if is_hex(num1):
        base = SEQUENCE_BASE
        print(num1)
        print(hex_to_sequence(num1, base))
        print(hex_to_decimal(num1))
        print(decimal_to_sequence(hex_to_decimal(num1), base))
        print(sequence_to_decimal(decimal_to_sequence(hex_to_decimal(num1), base), base))
        print(decimal_to_hex(hex_to_decimal(num1)))

if __name__ == "__main__":
    main("0X01C1FBA")
