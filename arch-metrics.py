import sys
from cmakeparser.parser import Parser
from cmakeparser.lexer import Lexer
        
lexer = Lexer()
parser = Parser()
node = parser.parse(sys.argv[1], lexer)
parser.walk(node, sys.argv[1])
