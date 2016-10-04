// Grammar for Femtocode

body: ';'* suite
suite: (assignment ';'*)* expression ';'*

assignment: NAME '=' closed_expression | fcnndef
fcnndef: 'def' NAME '(' paramlist ')' closed_exprsuite

expression: ifblock | fcndef | or_test
closed_expression: closed_ifblock | fcndef | or_test ';'

fcndef: '{' paramlist '=>' suite '}'
fcn1def: parameter '=>' (expression | '{' suite '}')
paramlist: (parameter ',')* (parameter [','])
parameter: NAME

exprsuite: (':' expression | [':'] '{' suite '}')
closed_exprsuite: (':' closed_expression | [':'] '{' suite '}')

ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' exprsuite)
closed_ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' closed_exprsuite)

or_test: and_test ('or' and_test)*
and_test: not_test ('and' not_test)*
not_test: 'not' not_test | comparison
comparison: arith_expr (comp_op arith_expr)*
comp_op: '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in'
arith_expr: term (('+' | '-') term)*
term: factor (('*' | '/' | '%' | '//') factor)*
factor: ('+' | '-') factor | power
power: atom trailer* ['**' factor]
atom: ('(' [expression] ')'
        | STRING
        | IMAG_NUMBER
        | FLOAT_NUMBER
        | HEX_NUMBER
        | OCT_NUMBER
        | DEC_NUMBER
        | ATARG
        | NAME)

trailer: '(' (arglist | fcn1def) ')' | '[' subscriptlist ']' | '.' NAME
subscriptlist: subscript (',' subscript)* [',']
subscript: expression | [expression] ':' [expression] [sliceop]
sliceop: ':' [expression]
arglist: (argument ',')* (argument [','])
argument: expression | NAME '=' expression
