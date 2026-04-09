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

    def read(self):
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
        p.read()
        return p

    def __next__(self):
        if len(self.file_stack) == 0:
            raise StopIteration

        while True:
            line = self.file_stack[-1].readline()

            if line.startswith("#"):
                continue

            if line == "":
                if len(self.file_stack) > 0:
                    self.file_stack.pop()
                else:
                    raise StopIteration

            opr = self.parse_line(line)
            self.instr_stack.append(opr)
            return opr


class Processor:

    def __init__(self, pre_processor):
        self.out_stack = []
        self.pre_processor = pre_processor
        self.registers = dict()
        self.sequence_stack = []
        self.sequence_item_counter_stack = []
        self.labels = dict()
        self.conditional_skip_depth = 0
        self.pc = 0

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

    def out(self):
        for opr in self.pre_processor:
            (operation, operand, extra) = opr

            if operation == "PUSH":
                self.out_stack.append(self.literal_to_value(operand))

            elif operation == "POP":
                if len(self.out_stack) > 0:
                    self.out_stack.pop()

            elif operation == "PEEK":
                if len(self.out_stack) > 0:
                    self.out_stack.append(self.out_stack[-1])

            elif operation == "STORE":
                if len(self.out_stack) > 0:
                    top = self.out_stack.pop()
                    alias = operand

                    if isinstance(top, list):
                        for i, val in enumerate(top):
                            self.registers[alias + "_" +
                                           str(i)] = self.value_to_literal(val)
                    else:
                        self.registers[alias] = self.value_to_literal(top)

            elif operation == "AND":
                if len(self.out_stack) > 2:
                    x = self.out_stack.pop()
                    y = self.out_stack.pop()
                    self.out_stack.append(AND(x, y))

            elif operation == "OR":
                if len(self.out_stack) > 2:
                    x = self.out_stack.pop()
                    y = self.out_stack.pop()
                    self.out_stack.append(OR(x, y))

            elif operation == "NOT":
                if len(self.out_stack) > 1:
                    self.out_stack[-1] = NOT(self.out_stack[-1])

            elif operation == "NAND":
                if len(self.out_stack) > 2:
                    x = self.out_stack.pop()
                    y = self.out_stack.pop()
                    self.out_stack.append(NAND(x, y))

            elif operation == "NOR":
                if len(self.out_stack) > 2:
                    x = self.out_stack.pop()
                    y = self.out_stack.pop()
                    self.out_stack.append(NOR(x, y))

            elif operation == "XOR":
                if len(self.out_stack) > 2:
                    x = self.out_stack.pop()
                    y = self.out_stack.pop()
                    self.out_stack.append(XOR(x, y))

            elif operation == "XNOR":
                if len(self.out_stack) > 2:
                    x = self.out_stack.pop()
                    y = self.out_stack.pop()
                    self.out_stack.append(XNOR(x, y))

            elif operation == "IF":
                if len(self.out_stack) > 0:
                    top = self.out_stack.pop()

                    #TODO: this is currently breaking as look ahead is removed for REPL
                    if not TRUTHY(top):
                        self.conditional_skip_depth = 1
                        while self.conditional_skip_depth > 0:
                            self.pc += 1
                            op = self.pre_processor.instr_stack[self.pc][0]

                            if op == "IF":
                                self.conditional_skip_depth += 1
                            elif op == "IF_END":
                                self.conditional_skip_depth -= 1
                        continue

            elif operation == "IF_END":
                pass

            elif operation == "LABEL":
                self.labels[operand] = self.pc

            elif operation == "GOTO":
                self.pc = self.labels[operand]
                continue

            elif operation == "DONE":
                break

            elif operation == "SEQUENCE":
                self.sequence_stack.append(operand)
                self.sequence_item_counter_stack.append(0)

            elif operation == "SEQUENCE_END":
                if len(self.out_stack) > 1 and len(self.sequence_item_counter_stack) > 0:
                    self.sequence_stack.pop()
                    self.sequence_item_counter_stack.pop()

            elif operation == "CLEAN":
                self.out_stack = []
                self.registers = dict()

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

        return self.out_stack

class Repl:
    def __init__(self):
        self.last_operation = ()
        self.pre_processor = PreProcessor(".")
        #self.pre_processor.file_stack.append(sys.stdin)
        self.pre_processor.file_stack.append(self)

    def __iter__(self):
        return self

    # duck typing
    def readline(self):
        return input(">>>> ")

    def __next__(self):
        try:
            opr = self.pre_processor.__next__() # this will call self.readline()
            #print(opr[0], opr[1], opr[2])

            operand = opr[0]
            if operand == "CLEAR":
                print(80*80*" ")
            elif operand == "DUMP":
                pass
            elif operand == "RESTART":
                self.__init__()


            return opr
        except KeyboardInterrupt:
            print()
            print("=================================")
            raise StopIteration



if __name__ == "__main__":
    pass


