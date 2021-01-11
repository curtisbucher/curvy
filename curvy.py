import ast
from collections import defaultdict
from itertools import count
import builtins
import traceback

def main(vm, user_input):
    tree = ast.parse(user_input)
    compiler = Compiler()

    # Optimizing tree
    optimizer = Optimizer()
    tree = optimizer.visit(tree)

    # Compiling tree and building bytecode
    compiler.visit(tree)
    bytecode = compiler.build()

    # Runing bytecode in the virtual machine
    vm.run(bytecode)


class Code:
    def __init__(self, names, consts, code):
        self.names = names  # Variable Names for whole code
        self.consts = consts  # Constants for whole code
        self.code = code  # Byte string [opcode, oparg]


# Data
OPNAMES = [
    "LOAD_CONST",
    "PRINT_EXPR",
    "DUP_TOP",
    "POP_TOP",
    "LOAD_NAME",
    "STORE_NAME",
    "DEL_NAME",
    "BUILD_LIST",
    "BUILD_TUPLE",
    "BUILD_SET",
    "BUILD_DICT",
    "BINARY_ADD",
    "BINARY_SUB",
    "BINARY_DIV",
    "BINARY_MUL",
    "BINARY_MOD",
    "BINARY_POW",  # **
    "BINARY_FLOORDIV",  # //
    "BIT_AND",
    "BIT_OR",
    "BIT_XOR",
    "LSHIFT",
    "RSHIFT",
    "UNARY_ADD",
    "UNARY_SUB",
    "UNARY_NOT",
    "UNARY_INVERT",
    "INDEX",
    "EXTENDED_ARG",  # args larger than 255
    "JUMP",
    "JUMP_IF_FALSE",
    "GET_ITER", # pops the top of the stack, turns it into an iterator and puts it back on top of the stack
    "FOR_ITER", # Will either call next() on the top of the stack (hopefully its an iterator). If the iterator is exausted, jump to the arg
    "CALL_FUNCTION",
]

OPCODES = {opname: opcode for opcode, opname in enumerate(OPNAMES)}


class Optimizer(ast.NodeTransformer):
    """ Given an AST, optimizes things that dont need to be compiled. Inheritance takes care of visiting functions from tree."""

    def visit_BinOp(self, node):
        """ Optimizes BinOp nodes between two constants """
        node = self.generic_visit(node)
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            if isinstance(node.op, ast.Add):
                return ast.Constant(node.left.value + node.right.value)
            elif isinstance(node.op, ast.Sub):
                return ast.Constant(node.left.value - node.right.value)
            elif isinstance(node.op, ast.Mult):
                return ast.Constant(node.left.value * node.right.value)
            elif isinstance(node.op, ast.Div):
                return ast.Constant(node.left.value / node.right.value)
            elif isinstance(node.op, ast.FloorDiv):
                return ast.Constant(node.left.value // node.right.value)
            elif isinstance(node.op, ast.Mod):
                return ast.Constant(node.left.value % node.right.value)
            elif isinstance(node.op, ast.Pow):
                return ast.Constant(node.left.value ** node.right.value)
            elif isinstance(node.op, ast.BitAnd):
                return ast.Constant(node.left.value & node.right.value)
            elif isinstance(node.op, ast.BitOr):
                return ast.Constant(node.left.value | node.right.value)
            elif isinstance(node.op, ast.BitXor):
                return ast.Constant(node.left.value ^ node.right.value)
            elif isinstance(node.op, ast.LShift):
                return ast.Constant(node.left.value << node.right.value)
            elif isinstance(node.op, ast.RShift):
                return ast.Constant(node.left.value >> node.right.value)
        return node

    def visit_Tuple(self, node):
        """ Optimizes building tuple of only constants."""
        self.generic_visit(node)
        new_elts = []
        for child in node.elts:
            # Optimizing child nodes, for nested constants
            if not isinstance(child, ast.Constant):
                return node
            new_elts.append(child.value)
        return ast.Constant(tuple(new_elts))


class Compiler:
    def __init__(self):
        self.names = defaultdict(count().__next__)
        self.consts = defaultdict(count().__next__)
        self.code = []
        self.labels = {}

    def build(self):
        for x in range(len(self.code)):
            # If the item is a marker (represented by an object that is not an integer)
            if not isinstance(self.code[x], int):
                # Assign the marker (the arg in a jump argument) to be the location to jump to
                self.code[x] = self.labels[self.code[x]]

        return Code(
            tuple(self.names), tuple(v for t, v in self.consts), bytes(self.code)
        )

    def add_name(self, name) -> int:
        return self.names[name]

    def add_const(self, const) -> int:
        return self.consts[type(const), const]

    def emit(self, opname, oparg):
        # Appending two items to the end of the list, not a tuple

        # Getting a list of bytes in the oparg, from least to greatest
        opbytes = []
        while oparg:
            opbytes.append(oparg & 255)
            oparg = oparg >> 8

        for b in opbytes[:0:-1]:
            self.code += (OPCODES["EXTENDED_ARG"], b)

        if not opbytes:
            opbytes = [0]

        ## Operating on the bottom byte
        self.code += (OPCODES[opname], opbytes[0])

    def emit_jump(self, opname, marker):
        self.code += (OPCODES[opname], marker)

    def label(self, marker):
        # Set a marker for a jump at the current position in the code.
        # Set marker in self.labels
        assert marker not in self.labels
        self.labels[marker] = len(self.code) // 2

    def visit(self, node):
        if not isinstance(node, list):
            node = [node]

        for child in node:
            handler = getattr(self, f"visit_{child.__class__.__name__}")
            handler(child)

    def visit_Module(self, node):
        # For compiling a module
        for child in node.body:
            self.visit(child)

    def visit_Interactive(self, node): # pragma: no cover
        # For compiling an interactive interpreter
        for child in node.body:
            self.visit(child)

    def visit_Expr(self, node):
        self.visit(node.value)
        self.emit("PRINT_EXPR", 0)

    def visit_Assign(self, node):
        self.visit(node.value)
        assert node.targets, "need at least one target!"
        for target in node.targets[:-1]:
            self.emit("DUP_TOP", 0)
            self.visit(target)
        self.visit(node.targets[-1])

    def visit_Constant(self, node):
        self.emit("LOAD_CONST", self.add_const(node.value))

    def visit_Name(self, node):
        oparg = self.add_name(node.id)
        if isinstance(node.ctx, ast.Store):
            self.emit("STORE_NAME", oparg)
        elif isinstance(node.ctx, ast.Load):
            self.emit("LOAD_NAME", oparg)
        else:
            assert False, node.ctx  # pragma: no cover

    def visit_Delete(self, node):
        for target in node.targets:
            self.emit("DEL_NAME", self.add_name(target.id))

    def visit_Tuple(self, node):
        for child in node.elts:
            self.visit(child)
        self.emit("BUILD_TUPLE", len(node.elts))

    def visit_List(self, node):
        for child in node.elts:
            self.visit(child)
        self.emit("BUILD_LIST", len(node.elts))

    def visit_Set(self, node):
        for child in node.elts:
            self.visit(child)
        self.emit("BUILD_SET", len(node.elts))

    def visit_Dict(self, node):
        for x in range(len(node.keys)):
            self.visit(node.values[x])
            self.visit(node.keys[x])
        self.emit("BUILD_DICT", len(node.keys))

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.op)

    def visit_Add(self, node):
        self.emit("BINARY_ADD", 0)

    def visit_Sub(self, node):
        self.emit("BINARY_SUB", 0)

    def visit_Div(self, node):
        self.emit("BINARY_DIV", 0)

    def visit_Mult(self, node):
        self.emit("BINARY_MUL", 0)

    def visit_Mod(self, node):
        self.emit("BINARY_MOD", 0)

    def visit_FloorDiv(self, node):
        self.emit("BINARY_FLOORDIV", 0)

    def visit_Pow(self, node):
        self.emit("BINARY_POW", 0)

    def visit_BitAnd(self, node):
        self.emit("BIT_AND", 0)

    def visit_BitOr(self, node):
        self.emit("BIT_OR", 0)

    def visit_BitXor(self, node):
        self.emit("BIT_XOR", 0)

    def visit_LShift(self, node):
        self.emit("LSHIFT", 0)

    def visit_RShift(self, node):
        self.emit("RSHIFT", 0)

    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        self.visit(node.op)

    def visit_UAdd(self, node):
        self.emit("UNARY_ADD", 0)

    def visit_USub(self, node):
        self.emit("UNARY_SUB", 0)

    def visit_Not(self, node):
        self.emit("UNARY_NOT", 0)

    def visit_Invert(self, node):
        self.emit("UNARY_INVERT", 0)

    def visit_AugAssign(self, node):
        # Loading value from name
        self.visit(ast.Name(node.target.id, ast.Load()))
        # Operating
        self.visit(node.value)
        self.visit(node.op)
        # Storing value
        self.visit(ast.Name(node.target.id, ast.Store()))

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Index(self, node):
        self.visit(node.value)
        self.emit("INDEX", 0)

    def visit_IfExp(self, node):
        mark_else = object()
        mark_end = object()
        # test, body, orelse
        self.visit(node.test)
        self.emit_jump("JUMP_IF_FALSE", mark_else)
        self.emit("POP_TOP", 0)
        self.visit(node.body)
        self.emit_jump("JUMP", mark_end)
        self.label(mark_else)
        self.emit("POP_TOP", 0)
        self.visit(node.orelse)
        self.label(mark_end)

    def visit_If(self, node):
        self.visit_IfExp(node)

    def visit_While(self, node):
        mark_loop = object()
        mark_end = object()
        self.label(mark_loop)
        self.visit(node.test)
        self.emit_jump("JUMP_IF_FALSE", mark_end)
        self.emit("POP_TOP", 0)
        self.visit(node.body)
        self.emit_jump("JUMP", mark_loop)
        self.label(mark_end)
        self.emit("POP_TOP", 0)

    def visit_For(self, node):
        assert not node.orelse, "we don't support this."
        mark_loop = object()
        mark_end = object()

        self.visit(node.iter) # for a in b<<
        self.emit("GET_ITER", 0)
        self.label(mark_loop)
        self.emit_jump("FOR_ITER", mark_end)
        self.visit(node.target) # for a<< in b
        self.visit(node.body) # the code in the loop
        self.emit_jump("JUMP", mark_loop)
        self.label(mark_end)
        self.emit("POP_TOP", 0) # Taking care of the empty iter on the stack

    def visit_Pass(self, node):
        pass

    def visit_Call(self, node):
        self.visit(node.func)
        self.visit(node.args)
        self.emit("CALL_FUNCTION", len(node.args))

class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.globals = {}
        self.builtins = vars(builtins)
        self.builtins["__name__"] = "__main__"
        self.bytecode = None
        self.oparg = 0
        self.pc = 0

    def run(self, bytecode):
        self.bytecode = bytecode
        real_oparg = 0
        self.pc = 0
        code = list(zip(bytecode.code[::2], bytecode.code[1::2]))

        while self.pc < len(code):
            opcode, oparg = code[self.pc]
            self.pc += 1
            real_oparg = (real_oparg << 8) + oparg
            if OPNAMES[opcode] == "EXTENDED_ARG":
                continue
            handler = getattr(self, f"visit_{OPNAMES[opcode]}")
            handler(real_oparg)
            real_oparg = 0

        assert not self.stack, "stack should be empty!"

    def visit_LOAD_CONST(self, oparg):
        self.stack.append(self.bytecode.consts[oparg])

    def visit_BINARY_ADD(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left + right)

    def visit_BINARY_SUB(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left - right)

    def visit_BINARY_MUL(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left * right)

    def visit_BINARY_DIV(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left / right)

    def visit_BINARY_MOD(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left % right)

    def visit_BINARY_POW(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left ** right)

    def visit_BINARY_FLOORDIV(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left // right)

    def visit_BIT_AND(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left & right)

    def visit_BIT_OR(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left | right)

    def visit_BIT_XOR(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left ^ right)

    def visit_LSHIFT(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left << right)

    def visit_RSHIFT(self, oparg):
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(left >> right)

    def visit_UNARY_ADD(self, oparg):
        operand = self.stack.pop()
        self.stack.append(+operand)

    def visit_UNARY_SUB(self, oparg):
        operand = self.stack.pop()
        self.stack.append(-operand)

    def visit_UNARY_NOT(self, oparg):
        operand = self.stack.pop()
        self.stack.append(not operand)

    def visit_UNARY_INVERT(self, oparg):
        operand = self.stack.pop()
        self.stack.append(~operand)

    def visit_PRINT_EXPR(self, oparg):
        output = self.stack.pop()
        if output is not None:
            print(repr(output))

    def visit_STORE_NAME(self, oparg):
        name = self.bytecode.names[oparg]
        self.globals[name] = self.stack.pop()

    def visit_LOAD_NAME(self, oparg):
        name = self.bytecode.names[oparg]

        if name in self.globals:
            self.stack.append(self.globals[name])
        elif name in self.builtins:
            self.stack.append(self.builtins[name])
        else:
            raise NameError(f"name {name!r} is not defined")

    def visit_DEL_NAME(self, oparg):
        name = self.bytecode.names[oparg]
        # Deleting in virtual machine
        del self.globals[name]

    def visit_DUP_TOP(self, oparg):
        self.stack.append(self.stack[-1])

    def visit_POP_TOP(self, oparg):
        self.stack.pop()

    def visit_BUILD_TUPLE(self, oparg):
        tup = []
        for x in range(oparg):
            tup.append(self.stack.pop())
        self.stack.append(tuple(tup[::-1]))

    def visit_BUILD_LIST(self, oparg):
        lst = []
        for x in range(oparg):
            lst.append(self.stack.pop())
        self.stack.append(lst[::-1])

    def visit_BUILD_SET(self, oparg):
        st = set()
        for x in range(oparg):
            st.add(self.stack.pop())
        self.stack.append(st)

    def visit_BUILD_DICT(self, oparg):
        dct = {}
        for x in range(oparg):
            key = self.stack.pop()
            value = self.stack.pop()
            dct[key] = value
        self.stack.append(dct)

    def visit_INDEX(self, oparg):
        index = self.stack.pop()
        value = self.stack.pop()
        self.stack.append(value[index])

    def visit_JUMP(self, oparg):
        self.pc = oparg

    def visit_JUMP_IF_FALSE(self, oparg):
        if not self.stack[-1]:
            self.pc = oparg

    def visit_GET_ITER(self, oparg):
        # Pops TOS, turns it into an iter, and pushes back to TOS
        top = self.stack.pop()
        self.stack.append(iter(top))

    def visit_FOR_ITER(self, oparg):
        # Will either call next() on the top of the stack (hopefully its an iterator). If the iterator is exausted, jump to the arg
        iterator = self.stack[-1]
        try:
            self.stack.append(next(iterator))
        except StopIteration:
            # If the iterator is exausted, jump
            self.pc = oparg

    def visit_CALL_FUNCTION(self, oparg):
        # Function calls. Oparg is the number of arguments on the stack, function is under all the args

        # Getting args from stack
        args = self.stack[-oparg:]
        self.stack = self.stack[:-oparg]

        # Get func from stack
        func = self.stack.pop()
        # Running function and appending return to stack
        self.stack.append(func(*args))

if __name__ == "__main__":  # pragma: no cover
    vm = VirtualMachine()
    while True:
        user_input = [input("~~: ")]
        while i := input("... "):
            user_input.append(i)
        try:
            main(vm, "\n".join(user_input))
        except SystemExit:
            break
        except BaseException:
            traceback.print_exc()

