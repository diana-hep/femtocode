# Grammar for Femtocode

suite: expression | assignment ';' suite

assignment: NAME '=' expression

expression: fcndef | fcndef '(' [arglist] ')' | ifblock | or_test

fcndef: '{' [paramlist] '=>' suite '}'
paramlist: (parameter ',')* (parameter [','])
parameter: NAME

ifblock: ('if' expression ':' (expression | '{' suite '}')
         ('elif' expression ':' (expression | '{' suite '}'))*
          'else' ':' (expression | '{' suite '}'))

or_test: and_test ('or' and_test)*
and_test: not_test ('and' not_test)*
not_test: 'not' not_test | comparison
comparison: arith_expr (comp_op arith_expr)*
comp_op: '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in'
arith_expr: term (( '+' | '-' ) term)*
term: factor (( '*' | '/' | '%' | '//' ) factor)*
factor: ('+' | '-') factor | power
power: atom trailer* ['**' factor]
atom: ('(' [expression] ')'
        | STRING
        | IMAG_NUMBER
        | FLOAT_NUMBER
        | HEX_NUMBER
        | OCT_NUMBER
        | DEC_NUMBER
        | NAME)

trailer: '(' [arglist] ')' | '[' subscriptlist ']' | '.' NAME
subscriptlist: subscript (',' subscript)* [',']
subscript: expression | [expression] ':' [expression] [sliceop]
sliceop: ':' [expression]
arglist: (argument ',')* (argument [','])
argument: expression | NAME '=' expression
