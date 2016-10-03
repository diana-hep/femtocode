# Grammar for Femtocode

suite: expression [';'] | assignment ';' suite

assignment: NAME '=' expression | fcnndef
fcnndef: 'def' NAME '(' paramlist ')' exprsuite

expression: ifblock | fcndef | or_test
exprsuite: (':' expression | [':'] '{' suite '}')

fcndef: '{' paramlist '=>' suite '}'
fcn1def: parameter '=>' suite
paramlist: (parameter ',')* (parameter [','])
parameter: NAME

ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' exprsuite)

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
        | fcndef '(' [arglist] ')'    # defining a function and immediately using it
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
