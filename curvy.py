import ast


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
    "LOAD_NAME",
    "STORE_NAME",
    "DEL",
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
        self.names = []
        self.consts = []
        self.code = []

    def build(self):
        return Code(tuple(self.names), tuple(self.consts), tuple(self.code))

    def emit(self, opname, oparg):
        # Appending two items to the end of the list, not a tuple
        self.code += (OPCODES[opname], oparg)

    def visit(self, node):
        handler = getattr(self, f"visit_{node.__class__.__name__}")
        handler(node)

    def visit_Module(self, node):
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
        self.emit("LOAD_CONST", len(self.consts))
        self.consts.append(node.value)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.emit("STORE_NAME", len(self.names))
        elif isinstance(node.ctx, ast.Load):
            self.emit("LOAD_NAME", len(self.names))
        else:
            assert False, node.ctx  # pragma: no cover
        self.names.append(node.id)

    def visit_Delete(self, node):
        for target in node.targets:
            self.names.append(target.id)
            self.emit("DEL", self.names.index(target.id))

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


class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.variables = {}
        self.bytecode = None

    def run(self, bytecode):
        self.bytecode = bytecode
        for opcode, oparg in zip(bytecode.code[::2], bytecode.code[1::2]):
            handler = getattr(self, f"visit_{OPNAMES[opcode]}")
            handler(oparg)
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
        print(self.stack.pop())

    def visit_STORE_NAME(self, oparg):
        name = self.bytecode.names[oparg]
        self.variables[name] = self.stack.pop()

    def visit_LOAD_NAME(self, oparg):
        name = self.bytecode.names[oparg]
        self.stack.append(self.variables[name])

    def visit_DEL(self, oparg):
        name = self.bytecode.names[oparg]
        # Deleting in virtual machine
        del self.variables[name]

    def visit_DUP_TOP(self, oparg):
        self.stack.append(self.stack[-1])

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


if __name__ == "__main__":  # pragma: no cover
    vm = VirtualMachine()
    while True:
        main(vm, input("~~ "))
