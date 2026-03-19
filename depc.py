import io
import copy
from pathlib import Path
from literals import *
from operations import *

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

            while operand in self.macros:
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

            return (operation, operand)

    def get(self):
        instr = []
        for command in self:
            instr.append(command)
        return instr


class Processor:
    def __init__(self, pre_processor):
        self.out_stack = [];
        self.instr_stack = []
        self.pre_processor = pre_processor;
        self.registers = dict()
        self.sequence_stack = []
        self.sequence_item_counter_stack = []
        self.labels = dict()

    def literal_to_value(self, literal: str):
        if literal == "ONE":
            return ONE
        elif literal == "ZERO":
            return ZERO
        else:
            if literal in self.registers:
                return self.literal_to_value(self.registers[literal])
            elif literal+"_0" in self.registers:
                sequence = []
                index = 0
                while literal+"_"+str(index) in self.registers:
                    sequence.append(self.literal_to_value(literal+"_"+str(index)))
                    index+=1
                return sequence
            elif is_hex(literal):
                return hex_to_sequence(literal, SEQUENCE_BASE)
            else:
                print(self.out_stack)
                print("Not implemented lit", literal)
                raise NotImplementedError

    def value_to_literal(self, value) -> str:
        if value == ONE or value == 1 or value == True:
            return "ONE"
        elif value == ZERO or value == 0 or value == False:
            return "ZERO"
        elif type(value) == type([]):
            return sequence_to_hex(value, SEQUENCE_BASE) 
        else:
            print(self.out_stack)
            print("Not implemented val", value)
            raise NotImplementedError


    def out(self):
        
        self.instr_stack = self.pre_processor.get()
        pc = 0
        #for command in self.pre_processor:
        while pc < len(self.instr_stack):

            command = self.instr_stack[pc]
            operation = command[0].upper()
            operand = command[1]

            if operation == "PUSH":
                self.out_stack.append(self.literal_to_value(operand)) 
            elif operation == "POP":
                self.out_stack.pop()
            elif operation == "PEEK":
                self.out_stack.append(self.out_stack[-1])
            elif operation == "STORE":
                top = self.out_stack.pop()
                alias = operand
                if type(top) == type([]):
                    for i, val in enumerate(top):
                        self.registers[alias+"_"+str(i)] = self.value_to_literal(val)
                else:
                    self.registers[alias] = self.value_to_literal(top)
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

            # conditionals 
            elif operation == "IF":
                top = self.out_stack.pop()
                self.if_condition_val = top
                if not TRUTHY(top):
                    # skip until IF_END
                    depth = 1
                    while depth > 0:
                        pc += 1
                        op = self.instr_stack[pc][0]
                        if op == "IF":
                            depth += 1
                        elif op == "IF_END":
                            depth -= 1
                    continue

            elif operation == "IF_END":
                """Do Nothing"""
            elif operation == "LABEL":
                alias = operand
                self.labels[alias] = pc 
            elif operation == "GOTO":
                label = operand
                instr = self.labels[label]
                pc = instr
                continue
            elif operation == "DONE":
                break

            # Data structures
            elif operation == "SEQUENCE":
               # If there should be name spaces within the sequence?
               # if len(self.sequence_stack) > 0:
               #     prefix = "::".join(self.sequence_stack)
               #     self.sequence_stack.append(prefix+"::"+operand)
               # else:
               #     self.sequence_stack.append(operand)
                self.sequence_stack.append(operand)
                self.sequence_item_counter_stack.append(0)
            elif operation == "SEQUENCE_END":
                self.sequence_stack.pop()
                self.sequence_item_counter_stack.pop()

            elif operation == "SHOW":
                for val in self.out_stack:
                    print(val)
         
            if len(self.sequence_stack) > 0:
               if(len(self.out_stack) > 0):
                   top = self.out_stack.pop() 
                   sequence_name = self.sequence_stack[-1]
                   item_index = self.sequence_item_counter_stack[-1]
                   item_name = sequence_name + "_" + str(item_index) 
                   self.sequence_item_counter_stack[-1] = item_index+1
                   self.registers[item_name] = self.value_to_literal(top)

            pc += 1

        return self.out_stack



if __name__ == '__module__':
    """ imported as a module """
