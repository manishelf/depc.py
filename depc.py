import io
import sys

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
        self.file_name = path.name

        self.file_stack = []
        self.instr_stack = []

    def load(self):
        try:
            content = read_file(self.path)
            file = io.StringIO(content)
            self.file_stack.append(file)
        except FileNotFoundError:
            print("unable to load ", self.path)

    def parse_line(self, line):
        line = line.strip()
        command = line.split(" ")

        operation = command[0].upper()
        operand = ""

        if len(command) > 1:
            operand = command[1]

        while operand in self.macros:
            operand = self.macros[operand]

        if operation == "INCLUDE":
            try:
                content = read_file(str(self.parent_dir) + "/" + operand)
                file = io.StringIO(content)
                self.file_stack.append(file)
                return (operation, operand, command[2:])
            except FileNotFoundError:
                print("unable to resolve import ", operand)
                raise StopIteration

        if operation == "DEFINE":
            alias = command[1]
            value = command[2]
            self.macros[alias] = value

        return (operation, operand, command[2:])

    def __iter__(self):
        p = PreProcessor(self.path)
        p.load()
        return p

    def __next__(self):
        if len(self.file_stack) == 0:
            raise StopIteration

        while True:

            if len(self.file_stack) == 0:
                raise StopIteration

            line = self.file_stack[-1].readline()

            if line.startswith("#"):
                continue

            if line == "":
                self.file_stack.pop()

            if line == "\n" or line == "\r" or line.strip() == "":
                continue

            opr = self.parse_line(line)
            self.instr_stack.append(opr)
            return opr


class Processor:

    def __init__(self, pre_processor):
        self.out_stack = []
        self.pre_processor = pre_processor
        self.instr_stack = pre_processor.instr_stack
        self.registers = dict()
        self.sequence_stack = []
        self.sequence_item_counter_stack = []
        self.labels = dict()
        self.conditional_skip_depth = 0
        self.pc = 0

        self.dispatch_table = dict() 
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_opcode"):
                self.dispatch_table[attr._opcode[0]] = attr._opcode[1:]
        
    # this is a closure
    def opcode(name, arity, consumer):
        def decorator(func):
            func._opcode = (name, func, arity, consumer)
            return func
        return decorator

    def literal_to_value(self, literal: str):
        if literal == "ONE" or literal == "one":
            return ONE
        elif literal == "ZERO" or literal == "zero":
            return ZERO
        else:
            if literal in self.registers:
                return self.literal_to_value(self.registers[literal])

            elif literal + "_0" in self.registers:
                sequence = []
                index = 0

                while literal + "_" + str(index) in self.registers:
                    sequence.append(
                        self.literal_to_value(literal + "_" + str(index))
                    )
                    index += 1

                return sequence

            elif is_hex(literal):
                return hex_to_sequence(literal, SEQUENCE_BASE)

            else:
                print(self.out_stack)
                print("Not implemented lit", literal)
                raise NotImplementedError

    def value_to_literal(self, value) -> str:
        if value in (ONE, 1, True):
            return "ONE"
        elif value in (ZERO, 0, False):
            return "ZERO"
        elif isinstance(value, list):
            return sequence_to_hex(value, SEQUENCE_BASE)
        elif isinstance(value, int):
            seq = decimal_to_sequence(value, SEQUENCE_BASE)
            return sequence_to_hex(seq, SEQUENCE_BASE)
        else:
            print(self.out_stack)
            print("Not implemented val", value)
            raise NotImplementedError

    @opcode("PUSH", 0, False)
    def PUSH(self, operand, arg):
        return self.literal_to_value(operand)

    @opcode("POP", 1, True)
    def POP(self, operand, arg):
        return None

    @opcode("PEEK", 1, False)
    def PEEK(self, operand, arg):
        return arg[0]

    @opcode("STORE", 1, True)
    def STORE(self, operand, arg):
        alias = operand

        if isinstance(arg[0], list):
            for i, val in enumerate(arg[0]):
                self.registers[alias + "_" +
                               str(i)] = self.value_to_literal(val)
        else:
            self.registers[alias] = self.value_to_literal(arg[0])

        return None

    @opcode("AND", 2, True)
    def AND(self, operand, arg):
        return AND(arg[0], arg[1])

    @opcode("OR", 2, True)
    def OR(self, operand, arg):
        return OR(arg[0], arg[1])

    @opcode("NOT", 1, True)
    def NOT(self, operand, arg):
        return NOT(arg[0])

    @opcode("XOR", 2, True)
    def XOR(self, operand, arg):
        return XOR(arg[0], arg[1])

    @opcode("NAND", 2, True)
    def NAND(self, operand, arg):
        return NAND(arg[0], arg[1])

    @opcode("NOR", 2, True)
    def NOR(self, operand, arg):
        return NOR(arg[0], arg[1])

    @opcode("XNOR", 2, True)
    def XNOR(self, operand, arg):
        return XNOR(arg[0], arg[1])


    def next_instr(self):
        if self.pc == len(self.instr_stack):
            opr = self.pre_processor.__next__()
        else:
            opr = self.instr_stack[self.pc]
        return opr

    def clk(self):
        
        try:
            (operation, operand, extra) = self.next_instr()
        except StopIteration:
            return False

        entry = self.dispatch_table.get(operation)
        if entry:
            (handler, arity, consumer) = entry
            args = []
            for i in range(0, arity):
                if len(self.out_stack) > 0:
                    if consumer:
                        val = self.out_stack.pop()
                    else:
                        val = self.out_stack[-1]
                    args.append(val)

            result = handler(self, operand, args)
            if result is not None:
                self.out_stack.append(result)

        elif operation == "IF":
            if len(self.out_stack) > 0:
                top = self.out_stack.pop()

                if not TRUTHY(top):
                    self.conditional_skip_depth = 1
                    # this will block CLK until if_end recieved
                    while self.conditional_skip_depth > 0:
                        self.pc += 1
                        try:
                            (op, _, _) = self.next_instr()
                        except StopIteration:
                            return False
                        if op == "IF":
                            self.conditional_skip_depth += 1
                        elif op == "IF_END":
                            self.conditional_skip_depth -= 1
                    return True

        elif operation == "IF_END":
            pass

        elif operation == "LABEL":
            self.labels[operand] = self.pc

        elif operation == "GOTO":
            self.pc = self.labels[operand]

        elif operation == "DONE":
            return False

        elif operation == "SEQUENCE":
            self.sequence_stack.append(operand)
            self.sequence_item_counter_stack.append(0)

        elif operation == "SEQUENCE_END":
            if len(self.out_stack) > 1 and len(self.sequence_item_counter_stack) > 0:
                self.sequence_stack.pop()
                self.sequence_item_counter_stack.pop()

        elif operation == "CLEAN":
            self.out_stack = []
            # self.registers = dict()

        elif operation == "SHOW":
            for val in self.out_stack:
                print(val)

        if len(self.sequence_stack) > 0 and len(self.out_stack) > 0:
            top = self.out_stack.pop()
            sequence_name = self.sequence_stack[-1]
            item_index = self.sequence_item_counter_stack[-1]

            item_name = sequence_name + "_" + str(item_index)
            self.sequence_item_counter_stack[-1] = item_index + 1

            self.registers[item_name] = self.value_to_literal(top)

        self.pc += 1
        return True

    def out(self):
        self.pre_processor.load()
        running = True
        while running:
            running = self.clk()
        return self.out_stack

class Repl:
    def __init__(self):
        self.last_operation = ("", "", [])
        self.pre_processor = PreProcessor(".")
        #self.pre_processor.file_stack.append(sys.stdin)
        self.pre_processor.file_stack.append(self)
        self.instr_stack = self.pre_processor.instr_stack;

    def __iter__(self):
        return self

    # duck typing
    def readline(self):
        return input(">>>> ")
    
    def load(self):
        print("Hello, welcome to Depc , checkout function.md to see available functions")

    def __next__(self):
        try:
            opr = self.pre_processor.__next__() # this will call self.readline()
            #print(opr[0], opr[1], opr[2])

            operation = opr[0]
            if operation == "CLEAR":
                print(80*80*" ")
            elif operation == "DUMP":
                pass
            elif operation == "RESTART":
                self.__init__()
            elif operation == ".":
                return self.last_operation

            self.last_operation = opr
            return opr
        except KeyboardInterrupt:
            print()
            print("=================================")
            raise StopIteration



if __name__ == "__main__":
    pass


