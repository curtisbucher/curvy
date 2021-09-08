import sys
import typing
import ast
import dis
import inspect

def print_help():
    print("usage: astbuddy [-s statement | -f file | -i ] ")
    print("-s stmt\t:", read_string.__doc__)
    print("-f file\t:", read_file.__doc__)
    print("-i\t:", read_interactive.__doc__)

def read_string(string):
    """Pretty print the AST of a program string passed as arg"""
    ##print(ast.dump(ast.parse(string)))
    pprint_ast(ast.parse(string))

def read_file(filename):
    """Dump the AST from a filename passed as arg. Likely very large output"""
    with open(filename, "r") as file:
        print(ast.dump(ast.parse(file.read())))

def read_interactive():
    """Pretty print the AST using interactive prompt [default]. """
    print("Entering interactive mode, type `q` to quit")

    statement = input(" - ")
    while statement != "q":
        print("AST")
        print(ast.dump(ast.parse(statement)))
        print("BYTECODE")
        print(dis.dis(statement))
        statement = input(" - ")

def pprint_ast(myast):
    for line in myast.body:
        pprint_node(line, 1)

def recur(myast):
    for key, var in myast.__dict__.items():
        print(key, var)

def pprint_node(node, depth):
    key_blacklist = ["lineno", "col_offset", "end_lineno", "end_col_offset"]

    print("\t" * (depth - 1) + "|---", type(node).__name__)
    for key, var in node.__dict__.items():

        if(key not in key_blacklist):
            print("\t" * (depth) + "|---", key, var)

        if(type(var) != list):
            var = [var]

        for v in var:
            if(inspect.getmodule(v) and inspect.getmodule(v).__name__ == "_ast"):
                pprint_node(v, depth + 2)



if __name__ == "__main__":
    options: typing.Dict[str, typing.Callable] = {
        "h" : print_help,
        "i" : read_interactive,
        "s" : read_string,
        "f" : read_file,
    }

    for x in range(len(sys.argv)):

        if(sys.argv[x][0] == "-"):
            if sys.argv[x][1] not in options:
                print("Unknown option:", sys.argv[x][1], "\n"
                    "usage: astbuddy [-s statement | -f file | -i ]", "\n"
                    "Try `astbuddy -h` for more information.")
                break

            elif sys.argv[x][1] in ["i", "h"]:
                options[sys.argv[x][1]]()
                break

            elif x >= len(sys.argv) - 1:
                print("Argument expected for the -" + sys.argv[x][1], "option")
                break

            else:
                options[sys.argv[x][1]](sys.argv[x+1])
