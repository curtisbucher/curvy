import ast


def main(vm, user_input):
    tree = ast.parse(user_input)
    compiler = Compiler()
    bytecode = list(compiler.visit(tree))
    vm.run(bytecode)


LOAD_CONST = "LOAD_CONST"
PRINT_EXPR = "PRINT_EXPR"
BINARY_ADD = "BINARY_ADD"
BINARY_SUB = "BINARY_SUB"
BINARY_DIV = "BINARY_DIV"
BINARY_MUL = "BINARY_MUL"
BINARY_MOD = "BINARY_MOD"
BINARY_POW = "BINARY_POW"
BINARY_FLOORDIV = "BINARY_FLOORDIV"
LOAD_NAME = "LOAD_NAME"
STORE_NAME = "STORE_NAME"
DUP_TOP = "DUP_TOP"



class Compiler:

    def visit(self, node):
        handler = getattr(self, f"visit_{node.__class__.__name__}")
        yield from handler(node)

    def visit_Module(self, node):
        for child in node.body:
            yield from self.visit(child)

    def visit_Expr(self, node):
        yield from self.visit(node.value)
        yield (PRINT_EXPR, None)

    def visit_Assign(self, node):
        yield from self.visit(node.value)
        assert node.targets, "need at least one target!"
        for target in node.targets[:-1]:
            yield (DUP_TOP, None)
            yield from self.visit(target)
        yield from self.visit(node.targets[-1])

    def visit_BinOp(self, node):
        yield from self.visit(node.left)
        yield from self.visit(node.right)
        yield from self.visit(node.op)

    def visit_Constant(self, node):
        yield (LOAD_CONST, node.value)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            yield (STORE_NAME, node.id)
        elif isinstance(node.ctx, ast.Load):
            yield (LOAD_NAME, node.id)
        else:
            assert False, node.ctx

    def visit_Add(self, node):
        yield (BINARY_ADD, None)

    def visit_Sub(self, node):
        yield (BINARY_SUB, None)

    def visit_Div(self, node):
        yield (BINARY_DIV, None)

    def visit_Mult(self, node):
        yield (BINARY_MUL, None)

    def visit_Mod(self, node):
        yield (BINARY_MOD, None)

    def visit_FloorDiv(self, node):
        yield (BINARY_FLOORDIV, None)

    def visit_Pow(self, node):
        yield (BINARY_POW, None)
    # Add bitwise operators

class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.names = {}

    def run(self, bytecode):
        for opcode, oparg in bytecode:
            handler = getattr(self, f"visit_{opcode}")
            handler(oparg)
        assert not self.stack, "stack should be empty!"

    def visit_LOAD_CONST(self, oparg):
        print(f"XXX: {oparg}")
        self.stack.append(oparg)

    def visit_BINARY_ADD(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b + a)

    def visit_BINARY_SUB(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b - a)

    def visit_BINARY_MUL(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b * a)

    def visit_BINARY_DIV(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b / a)

    def visit_BINARY_MOD(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b % a)

    def visit_BINARY_POW(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b ** a)

    def visit_BINARY_FLOORDIV(self, oparg):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(b // a)

    def visit_PRINT_EXPR(self, oparg):
        print(self.stack.pop())

    def visit_STORE_NAME(self, oparg):
        self.names[oparg] = self.stack.pop()

    def visit_LOAD_NAME(self, oparg):
        self.stack.append(self.names[oparg])

    def visit_DUP_TOP(self, oparg):
        self.stack.append(self.stack[-1])


if __name__ == "__main__":
    vm = VirtualMachine()
    while True:
        main(vm, input("~~ "))
