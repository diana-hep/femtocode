# Grammar for Femtocode

# funcdef: 'def' NAME parameters ':' suite
# parameters: '(' [paramlist] ')'
# paramlist: (parameter ',')* (parameter [','])
# parameter: NAME [':' expression]

# anonfuncdef: (param | parameters) '-' '>' suite

# suite: expression

# expression: and_test ('or' and_test)*
# and_test: not_test ('and' not_test)*
# not_test: 'not' not_test | comparison
# comparison: arith_expr (comp_op arith_expr)*
# comp_op: '<' | '>' | '=' '=' | '>' '=' | '<' '=' | '!' '=' | 'in' | 'not' 'in' | 'is' | 'is' 'not'
# arith_expr: term (( '+' | '-' ) term)*
# term: factor (( '*' | '/' | '%' | '/' '/' ) factor)*
# factor: ( '+' | '-' ) factor | power
# power: atom trailer* [ '*' '*' factor ]
# atom: '(' [expression] ')' | NAME | NUMBER | STRING
# trailer: '(' [arglist] ')' | '[' subscriptlist ']' | '.' NAME
# subscriptlist: subscript (',' subscript)* [',']
# subscript: expression | [expression] ':' [expression] [sliceop]
# sliceop: ':' [expression]

# arglist: (argument ',')* (argument [','])

# argument: expression | NAME '=' expression

atom: NAME | HEX_NUMBER | OCT_NUMBER | DEC_NUMBER | FLOAT_NUMBER | STRING
