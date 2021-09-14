![curvy_logo](https://www.curtisbucher.com/uploads/curvy_logo.png)

<h1 align="center"> ~~ The Curvy Homebrew Interpreter ~~</h1>

Curvy is an attempt to learn how CPython works under the hood, by attempting to rewrite much of the crucial code, while leveraging the existing CPython distribution to handle the nitty gritty details.

Ultimately, I hope to use curvy as a learning resource to implement gradually more of the interpreter as I progress in my knowledge.

### Progress

Currently, I am using CPython to generate an AST from python input, which I then hand to my rewritten optimizer, compiler and virtual machine. The challenge right now is to implement basic python functionality into my compiler and VM.

Currently, all elementary operations are supported, as well as a number of common data types, such as numbers, strings, lists, sets and dictionaries. Conditionals and loops are also supported.

### Screenshots

![carbon](https://www.curtisbucher.com/uploads/curvy_terminal.png)



