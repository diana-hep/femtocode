// Grammar for Femtocode

// Five shift/reduce conflicts resolved as shift, which is the right choice in each case.
// 
// WARNING: shift/reduce conflict for LPAR in state 121 resolved as shift
// WARNING: shift/reduce conflict for RSQB in state 144 resolved as shift
// WARNING: shift/reduce conflict for RSQB in state 187 resolved as shift
// WARNING: shift/reduce conflict for EQUAL in state 213 resolved as shift
// WARNING: shift/reduce conflict for COMMA in state 213 resolved as shift

body: ';'* suite
suite: (assignment ';'*)* expression ';'*

lvalues: (NAME ',')* NAME [',']                           // source of 1 shift/reduce conflict
assignment: lvalues '=' closed_expression | fcnndef
fcnndef: 'def' NAME '(' paramlist ')' closed_exprsuite

expression: ifblock | fcndef | or_test
closed_expression: closed_ifblock | fcndef | or_test ';'

fcndef: '{' paramlist '=>' suite '}'
fcn1def: parameter '=>' (expression | '{' suite '}')
paramlist: (parameter ',')* (parameter [','])
parameter: NAME ['=' expression]                          // source of 1 shift/reduce conflict

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
atom: ('(' expression ')'
        | '[' (expression ',')* [expression [',']] ']'    // source of 2 shift/reduce conflicts
        | fcndef '(' [arglist] ')'                        // source of 1 shift/reduce conflict
        | STRING
        | IMAG_NUMBER
        | FLOAT_NUMBER
        | HEX_NUMBER
        | OCT_NUMBER
        | DEC_NUMBER
        | ATARG
        | NAME)

trailer: '(' [arglist] ')' | '[' subscriptlist ']' | '.' NAME
subscriptlist: subscript (',' subscript)* [',']
subscript: expression | [expression] ':' [expression] [sliceop]
sliceop: ':' [expression]

arglist: ((argument ',')* (argument [','])) | fcn1def
argument: expression | NAME '=' expression
