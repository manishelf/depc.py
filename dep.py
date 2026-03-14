import io
from pathlib import Path

bitwise = False

def AND(x, y):
    if bitwise:
        return x & y
    else: 
        return int (x and y)

def OR(x, y):
    if bitwise:
        return x | y
    else: 
        return int (x or y)

def NOT(x):
    if bitwise:
        return ~x 
    else: 
        return int (not x) 

def NAND(x, y):
    return NOT(AND(x, y))

def NOR(x, y):
    return NOT(OR(x, y))

def XOR(x, y):
    return OR(AND(x, NOT(y)), AND(NOT(x), y))

def XNOR(x, y):
    return NOT(XOR(x, y))
    # return OR(AND(NOT(x), NOT(y)), AND(x, y)) 



def read_file(path: str) -> str:
    file = open(path, "r")
    content = file.read()
    file.close()
    return content


class PreProcessor:

    def __init__(self, file_path):
       self.macros = dict()
       path = Path(file_path)
       self.path = path
       self.parent_dir = path.parent
       self.file_name = path.name;
       self.file_stack = []

    def read(self):
       try:
           content = read_file(self.path)
           file = io.StringIO(content)
           self.file_stack.append(file)
       except FileNotFoundError:
           print("unable to load ", self.path)

    def __iter__(self):
        p = PreProcessor(self.path) 
        p.read()
        return p;

    def __next__(self):
        while True:
            
            if len(self.file_stack) == 0:
                raise StopIteration

            #line = self.file_stack[len(self.file_stack)-1].readline()
            line = self.file_stack[-1].readline()
            if line == "": #EOF
                self.file_stack.pop()

            line = line.strip()
            if not line or line.startswith("#"):   # skip single line comments
                continue
            command = line.split(" ")
            operation = command[0].upper()
            operand = "" 
            if len(command) > 1:
                operand = command[1]

            if operand in self.macros:
                operand = self.macros[operand]

            if operation == "INCLUDE":
                try:
                    content = read_file(str(self.parent_dir)+"/"+operand)
                    file = io.StringIO(content)
                    self.file_stack.append(file)
                    continue
                except FileNotFoundError:
                    print("unable to resolve import ", operand)
                    raise StopIteration

            if operation == "DEFINE":
                alias = command[1]
                value = command[2]
                self.macros[alias] = value

            if operation == "DONE":
                raise StopIteration

            return (operation, operand)


class Processor:
    def __init__(self, pre_processor):
        self.out_stack = [];
        self.pre_processor = pre_processor;

    def literal_to_value(self, literal: str) -> int:
        if literal == "ONE":
            return 1
        elif literal == "ZERO":
            return 0
        else:
            raise NotImplementedError

    def out(self):
        for command in self.pre_processor:
            operation = command[0].upper()
            operand = command[1]
            if operation == "PUSH":
                self.out_stack.append(self.literal_to_value(operand)) 
            elif operation == "POP":
                self.out_stack.pop()
            elif operation == "PEEK":
                self.out_stack.append(self.out_stack[-1])
            elif operation == "AND":
                x = self.out_stack.pop()
                y = self.out_stack.pop()
                self.out_stack.append(AND(x, y))
            elif operation == "OR":
                x = self.out_stack.pop()
                y = self.out_stack.pop()
                self.out_stack.append(OR(x, y))
            elif operation == "NOT":
                self.out_stack[-1] = NOT(self.out_stack[-1])
            elif operation == "NAND":
                x = self.out_stack.pop()
                y = self.out_stack.pop()
                self.out_stack.append(NAND(x, y))
            elif operation == "NOR":
                x = self.out_stack.pop()
                y = self.out_stack.pop()
                self.out_stack.append(NOR(x, y))
            elif operation == "XOR":
                x = self.out_stack.pop()
                y = self.out_stack.pop()
                self.out_stack.append(XOR(x, y))
            elif operation == "XNOR":
                x = self.out_stack.pop()
                y = self.out_stack.pop()
                self.out_stack.append(XNOR(x, y))

        return self.out_stack



if __name__ == '__module__':
    """ imported as a module """
