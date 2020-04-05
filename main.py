from lexer import Lexer
from parser import Parser

# Create lexer
lexer = Lexer()

# Load source into lexer
source = open('teste.c').read()
lexer.input(source)

# Print lexer tokens
for tok in lexer:
    print(tok)
print()

# Build the parser
parser = Parser(debug=False)
result = parser.parse(source)
print(result)


