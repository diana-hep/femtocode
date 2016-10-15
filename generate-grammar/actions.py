#!/usr/bin/env python

# Literally copied from Python's grammar: verified to produce the same AST and line numbers as Python 2.7.
actions = {}
actions['''or_test : and_test'''] = '''    p[0] = p[1]'''
actions['''or_test : and_test or_test_star'''] = '''    theor = Or()
    inherit_lineno(theor, p[2][0])
    p[0] = BoolOp(theor, [p[1]] + p[2])
    inherit_lineno(p[0], p[1])'''
actions['''or_test_star : OR and_test'''] = '''    p[0] = [p[2]]'''
actions['''or_test_star : or_test_star OR and_test'''] = '''    p[0] = p[1] + [p[3]]'''
actions['''and_test : not_test'''] = '''    p[0] = p[1]'''
actions['''and_test : not_test and_test_star'''] = '''    theand = And()
    inherit_lineno(theand, p[2][0])
    p[0] = BoolOp(theand, [p[1]] + p[2])
    inherit_lineno(p[0], p[1])'''
actions['''and_test_star : AND not_test'''] = '''    p[0] = [p[2]]'''
actions['''and_test_star : and_test_star AND not_test'''] = '''    p[0] = p[1] + [p[3]]'''
actions['''not_test : NOT not_test'''] = '''    thenot = Not()
    inherit_lineno(thenot, p[2])
    p[0] = UnaryOp(thenot, p[2], **p[1][1])'''
actions['''not_test : comparison'''] = '''    p[0] = p[1]'''
actions['''comp_op : LESS'''] = '''    p[0] = Lt()'''
actions['''comp_op : GREATER'''] = '''    p[0] = Gt()'''
actions['''comp_op : EQEQUAL'''] = '''    p[0] = Eq()'''
actions['''comp_op : GREATEREQUAL'''] = '''    p[0] = GtE()'''
actions['''comp_op : LESSEQUAL'''] = '''    p[0] = LtE()'''
actions['''comp_op : NOTEQUAL'''] = '''    p[0] = NotEq()'''
actions['''comp_op : IN'''] = '''    p[0] = In()'''
actions['''comp_op : NOT IN'''] = '''    p[0] = NotIn()'''
actions['''arith_expr : term'''] = '''    p[0] = p[1]'''
actions['''arith_expr : term arith_expr_star'''] = '''    p[0] = unwrap_left_associative([p[1]] + p[2], alt=len(p[2]) > 2)'''
actions['''arith_expr_star : PLUS term'''] = '''    p[0] = [Add(**p[1][1]), p[2]]'''
actions['''arith_expr_star : MINUS term'''] = '''    p[0] = [Sub(**p[1][1]), p[2]]'''
actions['''arith_expr_star : arith_expr_star PLUS term'''] = '''    p[0] = p[1] + [Add(**p[2][1]), p[3]]'''
actions['''arith_expr_star : arith_expr_star MINUS term'''] = '''    p[0] = p[1] + [Sub(**p[2][1]), p[3]]'''
actions['''term : factor'''] = '''    p[0] = p[1]'''
actions['''term : factor term_star'''] = '''    p[0] = unwrap_left_associative([p[1]] + p[2], alt=len(p[2]) > 2)'''
actions['''term_star : STAR factor'''] = '''    p[0] = [Mult(**p[1][1]), p[2]]'''
actions['''term_star : SLASH factor'''] = '''    p[0] = [Div(**p[1][1]), p[2]]'''
actions['''term_star : PERCENT factor'''] = '''    p[0] = [Mod(**p[1][1]), p[2]]'''
actions['''term_star : DOUBLESLASH factor'''] = '''    p[0] = [FloorDiv(**p[1][1]), p[2]]'''
actions['''term_star : term_star STAR factor'''] = '''    p[0] = p[1] + [Mult(**p[2][1]), p[3]]'''
actions['''term_star : term_star SLASH factor'''] = '''    p[0] = p[1] + [Div(**p[2][1]), p[3]]'''
actions['''term_star : term_star PERCENT factor'''] = '''    p[0] = p[1] + [Mod(**p[2][1]), p[3]]'''
actions['''term_star : term_star DOUBLESLASH factor'''] = '''    p[0] = p[1] + [FloorDiv(**p[2][1]), p[3]]'''
actions['''factor : PLUS factor'''] = '''    op = UAdd(**p[1][1])
    p[0] = UnaryOp(op, p[2])
    inherit_lineno(p[0], op)'''
actions['''factor : MINUS factor'''] = '''    if sys.version_info.major <= 2 and isinstance(p[2], Num) and not hasattr(p[2], "unary"):
        p[2].n *= -1
        p[0] = p[2]
        p[0].unary = True
        inherit_lineno(p[0], p[1][1])
    else:
        op = USub(**p[1][1])
        p[0] = UnaryOp(op, p[2])
        inherit_lineno(p[0], op)'''
actions['''factor : power'''] = '''    p[0] = p[1]'''
actions['''power : atom'''] = '''    p[0] = p[1]'''
actions['''power : atom DOUBLESTAR factor'''] = '''    p[0] = BinOp(p[1], Pow(**p[2][1]), p[3])
    inherit_lineno(p[0], p[1])'''
actions['''power : atom power_star'''] = '''    p[0] = unpack_trailer(p[1], p[2])'''
actions['''power : atom power_star DOUBLESTAR factor'''] = '''    p[0] = BinOp(unpack_trailer(p[1], p[2]), Pow(**p[3][1]), p[4])
    inherit_lineno(p[0], p[1])'''
actions['''power_star : trailer'''] = '''    p[0] = [p[1]]'''
actions['''power_star : power_star trailer'''] = '''    p[0] = p[1] + [p[2]]'''
actions['''trailer : LPAR arglist RPAR'''] = '''    p[0] = p[2]'''
actions['''trailer : LSQB subscriptlist RSQB'''] = '''    p[0] = Subscript(None, p[2], Load())'''
actions['''trailer : DOT NAME'''] = '''    p[0] = Attribute(None, p[2][0], Load())'''
actions['''subscriptlist : subscript'''] = '''    p[0] = p[1]'''
actions['''subscriptlist : subscript COMMA'''] = '''    if isinstance(p[1], Index):
        tup = Tuple([p[1].value], Load())
        inherit_lineno(tup, p[1].value)
        p[0] = Index(tup)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice([p[1]])
        inherit_lineno(p[0], p[1])'''
actions['''subscriptlist : subscript subscriptlist_star'''] = '''    args = [p[1]] + p[2]
    if all(isinstance(x, Index) for x in args):
        tup = Tuple([x.value for x in args], Load())
        inherit_lineno(tup, args[0].value)
        p[0] = Index(tup)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice(args)
        inherit_lineno(p[0], p[1])'''
actions['''subscriptlist : subscript subscriptlist_star COMMA'''] = '''    args = [p[1]] + p[2]
    if all(isinstance(x, Index) for x in args):
        tup = Tuple([x.value for x in args], Load())
        inherit_lineno(tup, args[0].value)
        p[0] = Index(tup)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice(args)
        inherit_lineno(p[0], p[1])'''
actions['''subscriptlist_star : COMMA subscript'''] = '''    p[0] = [p[2]]'''
actions['''subscriptlist_star : subscriptlist_star COMMA subscript'''] = '''    p[0] = p[1] + [p[3]]'''
actions['''subscript : COLON'''] = '''    p[0] = Slice(None, None, None, **p[1][1])'''
actions['''subscript : COLON sliceop'''] = '''    p[0] = Slice(None, None, p[2], **p[1][1])'''
actions['''sliceop : COLON'''] = '''    p[0] = Name("None", Load(), **p[1][1]) if sys.version_info.major <= 2 else None'''

# Different from pure Python merely for spelling (names in femtocode.g)
actions['''expression : ifblock'''] = '''    p[0] = p[1]'''
actions['''expression : fcndef'''] = '''    p[0] = p[1]'''
actions['''expression : or_test'''] = '''    p[0] = p[1]'''
actions['''closed_expression : closed_ifblock'''] = '''    p[0] = p[1]'''
actions['''closed_expression : fcndef'''] = '''    p[0] = p[1]'''
actions['''closed_expression : or_test SEMI'''] = '''    p[0] = p[1]'''

actions['''comparison : arith_expr'''] = '''    p[0] = p[1]'''
actions['''comparison : arith_expr comparison_star'''] = '''    ops, exprs = p[2]
    p[0] = Compare(p[1], ops, exprs)
    inherit_lineno(p[0], p[1])'''
actions['''comparison_star : comp_op arith_expr'''] = '''    inherit_lineno(p[1], p[2])
    p[0] = ([p[1]], [p[2]])'''
actions['''comparison_star : comparison_star comp_op arith_expr'''] = '''    ops, exprs = p[1]
    inherit_lineno(p[2], p[3])
    p[0] = (ops + [p[2]], exprs + [p[3]])'''

actions['''trailer : LPAR RPAR'''] = '''    p[0] = FcnCall(None, [], [], [], **p[1][1])'''

actions['''subscript : expression'''] = '''    p[0] = Index(p[1])
    inherit_lineno(p[0], p[1])'''
actions['''subscript : COLON'''] = '''    p[0] = Slice(None, None, None, **p[1][1])'''
actions['''subscript : COLON sliceop'''] = '''    p[0] = Slice(None, None, p[2], **p[1][1])'''
actions['''subscript : COLON expression'''] = '''    p[0] = Slice(None, p[2], None, **p[1][1])'''
actions['''subscript : COLON expression sliceop'''] = '''    p[0] = Slice(None, p[2], p[3], **p[1][1])'''
actions['''subscript : expression COLON'''] = '''    p[0] = Slice(p[1], None, None)
    inherit_lineno(p[0], p[1])'''
actions['''subscript : expression COLON sliceop'''] = '''    p[0] = Slice(p[1], None, p[3])
    inherit_lineno(p[0], p[1])'''
actions['''subscript : expression COLON expression'''] = '''    p[0] = Slice(p[1], p[3], None)
    inherit_lineno(p[0], p[1])'''
actions['''subscript : expression COLON expression sliceop'''] = '''    p[0] = Slice(p[1], p[3], p[4])
    inherit_lineno(p[0], p[1])'''
actions['''sliceop : COLON expression'''] = '''    p[0] = p[2]'''

actions['''atom : LPAR expression RPAR'''] = '''    p[0] = p[2]
    p[0].alt = p[1][1]'''

actions['''atom : LSQB RSQB'''] = '''    p[0] = List([], Load(), **p[1][1])'''
actions['''atom : LSQB expression RSQB'''] = '''    p[0] = List([p[2]], Load(), **p[1][1])'''
actions['''atom : LSQB expression COMMA RSQB'''] = '''    p[0] = List([p[2]], Load(), **p[1][1])'''
actions['''atom : LSQB atom_star RSQB'''] = '''    p[0] = List(p[2], Load(), **p[1][1])'''
actions['''atom : LSQB atom_star expression RSQB'''] = '''    p[2].append(p[3])
    p[0] = List(p[2], Load(), **p[1][1])'''
actions['''atom : LSQB atom_star expression COMMA RSQB'''] = '''    p[2].append(p[3])
    p[0] = List(p[2], Load(), **p[1][1])'''
actions['''atom_star : expression COMMA'''] = '''    p[0] = [p[1]]'''
actions['''atom_star : atom_star expression COMMA'''] = '''    p[1].append(p[2])
    p[0] = p[1]'''

actions['''atom : fcndef LPAR RPAR'''] = '''    p[0] = FcnCall(p[1], [], [], [])
    inherit_lineno(p[0], p[1])'''
actions['''atom : fcndef LPAR arglist RPAR'''] = '''
    p[0] = p[3]
    p[0].function = p[1]'''
actions['''atom : MULTILINESTRING'''] = '''    p[0] = Str(p[1][0], **p[1][1])'''
actions['''atom : STRING'''] = '''    p[0] = Str(p[1][0], **p[1][1])'''
actions['''atom : IMAG_NUMBER'''] = '''    p[0] = Num(p[1][0], **p[1][1])'''
actions['''atom : FLOAT_NUMBER'''] = '''    p[0] = Num(p[1][0], **p[1][1])'''
actions['''atom : HEX_NUMBER'''] = '''    p[0] = Num(p[1][0], **p[1][1])'''
actions['''atom : OCT_NUMBER'''] = '''    p[0] = Num(p[1][0], **p[1][1])'''
actions['''atom : DEC_NUMBER'''] = '''    p[0] = Num(p[1][0], **p[1][1])'''
actions['''atom : ATARG'''] = '''    p[0] = AtArg(p[1][0], **p[1][1])'''
actions['''atom : NAME'''] = '''    p[0] = Name(p[1][0], Load(), **p[1][1])'''

# Different from Python in behavior; fill Femtocode ASTs, not Python
actions['''body : suite'''] = '''    p[0] = p[1]'''
actions['''body : body_star suite'''] = '''    p[0] = p[2]'''
actions['''body_star : SEMI'''] = '''    p[0] = p[1]'''
actions['''body_star : body_star SEMI'''] = '''    p[0] = p[2]'''

actions['''suite : expression'''] = '''    p[0] = Suite([], p[1])
    inherit_lineno(p[0], p[1])'''
actions['''suite : expression'''] = '''    p[0] = Suite([], p[1])
    inherit_lineno(p[0], p[1])'''
actions['''suite : expression suite_star'''] = '''    p[0] = Suite([], p[1])
    inherit_lineno(p[0], p[1])'''
actions['''suite : suite_star2 expression'''] = '''    p[0] = Suite(p[1], p[2])
    inherit_lineno(p[0], p[1][0])'''
actions['''suite : suite_star2 expression suite_star3'''] = '''    p[0] = Suite(p[1], p[2])
    inherit_lineno(p[0], p[1][0])'''
actions['''suite_star : SEMI'''] = '''    p[0] = None'''
actions['''suite_star : suite_star SEMI'''] = '''    p[0] = None'''
actions['''suite_star3 : SEMI'''] = '''    p[0] = None'''
actions['''suite_star3 : suite_star3 SEMI'''] = '''    p[0] = None'''
actions['''suite_star2 : assignment'''] = '''    p[0] = [p[1]]'''
actions['''suite_star2 : assignment suite_star2_star'''] = '''    p[0] = [p[1]]'''
actions['''suite_star2 : suite_star2 assignment'''] = '''    p[0] = p[1] + [p[2]]'''
actions['''suite_star2 : suite_star2 assignment suite_star2_star'''] = '''    p[0] = p[1] + [p[2]]'''
actions['''suite_star2_star : SEMI'''] = '''    p[0] = None'''
actions['''suite_star2_star : suite_star2_star SEMI'''] = '''    p[0] = None'''

actions['''lvalues : NAME'''] = '''    p[0] = [Name(p[1][0], Store(), **p[1][1])]'''
actions['''lvalues : NAME COMMA'''] = '''    p[0] = [Name(p[1][0], Store(), **p[1][1])]'''
actions['''lvalues : lvalues_star NAME'''] = '''    p[0] = p[1] + [Name(p[2][0], Store(), **p[2][1])]'''
actions['''lvalues : lvalues_star NAME COMMA'''] = '''    p[0] = p[1] + [Name(p[2][0], Store(), **p[2][1])]'''
actions['''lvalues_star : NAME COMMA'''] = '''    p[0] = [Name(p[1][0], Store(), **p[1][1])]'''
actions['''lvalues_star : lvalues_star NAME COMMA'''] = '''    p[0] = p[1] + [Name(p[2][0], Store(), **p[2][1])]'''

actions['''assignment : lvalues EQUAL closed_expression'''] = '''    p[0] = Assignment(p[1], p[3])
    inherit_lineno(p[0], p[1][0])'''
actions['''assignment : fcnndef'''] = '''    p[0] = p[1]'''

actions['''fcnndef : DEF NAME LPAR RPAR closed_exprsuite'''] = '''    p[0] = Assignment([Name(p[2][0], Store(), **p[2][1])], FcnDef([], [], p[5], **p[1][1]), **p[1][1])'''
actions['''fcnndef : DEF NAME LPAR paramlist RPAR closed_exprsuite'''] = '''    fcndef = p[4]
    fcndef.body = p[6]
    p[0] = Assignment([Name(p[2][0], Store(), **p[2][1])], fcndef, **p[1][1])'''
actions['''fcndef : LBRACE RIGHTARROW suite RBRACE'''] = '''    p[0] = FcnDef([], [], p[3], **p[1][1])'''
actions['''fcndef : LBRACE paramlist RIGHTARROW suite RBRACE'''] = '''    p[0] = p[2]
    p[0].body = p[4]'''
actions['''fcn1def : parameter RIGHTARROW expression'''] = '''    p[0] = p[1]
    p[0].body = Suite([], p[3])
    inherit_lineno(p[0].body, p[3])'''
actions['''fcn1def : parameter RIGHTARROW LBRACE suite RBRACE'''] = '''
    p[0] = p[1]
    p[0].body = p[4]'''

actions['''paramlist : parameter'''] = '''    p[0] = p[1]'''
actions['''paramlist : parameter COMMA'''] = '''    p[0] = p[1]'''
actions['''paramlist : paramlist_star parameter'''] = '''    p[0] = p[1]
    p[0].parameters.extend(p[2].parameters)
    p[0].defaults.extend(p[2].defaults)'''
actions['''paramlist : paramlist_star parameter COMMA'''] = '''    p[0] = p[1]
    p[0].parameters.extend(p[2].parameters)
    p[0].defaults.extend(p[2].defaults)'''
actions['''paramlist_star : parameter COMMA'''] = '''    p[0] = p[1]'''
actions['''paramlist_star : paramlist_star parameter COMMA'''] = '''    p[0] = p[1]
    p[0].parameters.extend(p[2].parameters)
    p[0].defaults.extend(p[2].defaults)'''
actions['''parameter : NAME'''] = '''    p[0] = FcnDef([Name(p[1][0], Param(), **p[1][1])], [None], None, **p[1][1])'''
actions['''parameter : NAME EQUAL expression'''] = '''    p[0] = FcnDef([Name(p[1][0], Param(), **p[1][1])], [p[3]], None, **p[1][1])'''

actions['''exprsuite : COLON expression'''] = '''    p[0] = Suite([], p[2])
    inherit_lineno(p[0], p[2])'''
actions['''exprsuite : LBRACE suite RBRACE'''] = '''    p[0] = p[2]'''
actions['''exprsuite : COLON LBRACE suite RBRACE'''] = '''    p[0] = p[3]'''
actions['''closed_exprsuite : COLON closed_expression'''] = '''    p[0] = Suite([], p[2])
    inherit_lineno(p[0], p[2])'''
actions['''closed_exprsuite : LBRACE suite RBRACE'''] = '''    p[0] = p[2]'''
actions['''closed_exprsuite : COLON LBRACE suite RBRACE'''] = '''    p[0] = p[3]'''

actions['''ifblock : IF expression exprsuite ELSE exprsuite'''] = '''    p[0] = IfChain([p[2]], [p[3]], p[5], **p[1][1])'''
actions['''ifblock : IF expression exprsuite ifblock_star ELSE exprsuite'''] = '''    p[0] = IfChain([p[2]] + p[4][0], [p[3]] + p[4][1], p[6], **p[1][1])'''
actions['''ifblock_star : ELIF expression exprsuite'''] = '''    p[0] = ([p[2]], [p[3]])'''
actions['''ifblock_star : ifblock_star ELIF expression exprsuite'''] = '''
    p[0] = p[1]
    p[0][0].append(p[3])
    p[0][1].append(p[4])'''
actions['''closed_ifblock : IF expression exprsuite ELSE closed_exprsuite'''] = '''    p[0] = IfChain([p[2]], [p[3]], p[5], **p[1][1])'''
actions['''closed_ifblock : IF expression exprsuite closed_ifblock_star ELSE closed_exprsuite'''] = '''    p[0] = IfChain([p[2]] + p[4][0], [p[3]] + p[4][1], p[6], **p[1][1])'''
actions['''closed_ifblock_star : ELIF expression exprsuite'''] = '''    p[0] = ([p[2]], [p[3]])'''
actions['''closed_ifblock_star : closed_ifblock_star ELIF expression exprsuite'''] = '''    p[0] = p[1]
    p[0][0].append(p[3])
    p[0][1].append(p[4])'''

actions['''arglist : argument'''] = '''    p[0] = p[1]'''
actions['''arglist : argument COMMA'''] = '''    p[0] = p[1]'''
actions['''arglist : arglist_star argument'''] = '''    p[0] = p[1]
    p[0].positional.extend(p[2].positional)
    p[0].names.extend(p[2].names)
    p[0].named.extend(p[2].named)'''
actions['''arglist : arglist_star argument COMMA'''] = '''    p[0] = p[1]
    p[0].positional.extend(p[2].positional)
    p[0].names.extend(p[2].names)
    p[0].named.extend(p[2].named)'''
actions['''arglist : fcn1def'''] = '''    p[0] = FcnCall(None, [p[1]], [], [])
    inherit_lineno(p[0], p[1])'''
actions['''arglist_star : argument COMMA'''] = '''    p[0] = p[1]'''
actions['''arglist_star : arglist_star argument COMMA'''] = '''    p[0] = p[1]
    p[0].positional.extend(p[2].positional)
    p[0].names.extend(p[2].names)
    p[0].named.extend(p[2].named)'''
actions['''argument : expression'''] = '''    p[0] = FcnCall(None, [p[1]], [], [])
    inherit_lineno(p[0], p[1])'''
actions['''argument : NAME EQUAL expression'''] = '''    p[0] = FcnCall(None, [], [Name(p[1][0], Param(), **p[1][1])], [p[3]], **p[1][1])'''

# Didn't use these: tried putting optional semicolons at the beginning of suite
actions['''suite : suite_star4 expression'''] = '''    p[0] = p[2]'''
actions['''suite : suite_star4 expression suite_star5'''] = '''    p[0] = p[2]'''
actions['''suite : suite_star4 suite_star6 expression'''] = '''    p[0] = Suite(p[2], p[3])
    inherit_lineno(p[0], p[2][0] if len(p[2]) > 0 else p[3])'''
actions['''suite : suite_star4 suite_star6 expression suite_star7'''] = '''    p[0] = Suite(p[2], p[3])
    inherit_lineno(p[0], p[2][0] if len(p[2]) > 0 else p[3])'''
actions['''suite_star5 : SEMI'''] = '''    p[0] = None'''
actions['''suite_star5 : suite_star5 SEMI'''] = '''    p[0] = None'''
actions['''suite_star7 : SEMI'''] = '''    p[0] = None'''
actions['''suite_star7 : suite_star7 SEMI'''] = '''    p[0] = None'''
actions['''suite_star6 : assignment'''] = '''    p[0] = [p[1]]'''
actions['''suite_star6 : assignment suite_star6_star'''] = '''    p[0] = [p[1]]'''
actions['''suite_star6 : suite_star6 assignment'''] = '''    p[1].append(p[2])
    p[0] = p[1]'''
actions['''suite_star6 : suite_star6 assignment suite_star6_star'''] = '''    p[1].append(p[2])
    p[0] = p[1]'''
actions['''suite_star4 : SEMI'''] = '''    p[0] = None'''
actions['''suite_star4 : suite_star4 SEMI'''] = '''    p[0] = None'''
actions['''suite_star6_star : SEMI'''] = '''    p[0] = None'''
actions['''suite_star6_star : suite_star6_star SEMI'''] = '''    p[0] = None'''

# tried putting optional semicolons at every site where suite is used
actions['''fcndef : LBRACE RIGHTARROW fcndef_star suite RBRACE'''] = '''    p[0] = FcnDef([], [], p[4], **p[1][1])'''
actions['''fcndef : LBRACE paramlist RIGHTARROW fcndef_star2 suite RBRACE'''] = '''    p[0] = p[2]
    p[0].body = p[5]'''
actions['''fcndef_star : SEMI'''] = '''    p[0] = None'''
actions['''fcndef_star : fcndef_star SEMI'''] = '''    p[0] = None'''
actions['''fcndef_star2 : SEMI'''] = '''    p[0] = None'''
actions['''fcndef_star2 : fcndef_star2 SEMI'''] = '''    p[0] = None'''
actions['''exprsuite : LBRACE exprsuite_star suite RBRACE'''] = '''    p[0] = p[3]'''
actions['''exprsuite : COLON LBRACE exprsuite_star2 suite RBRACE'''] = '''    p[0] = p[4]'''
actions['''exprsuite_star : SEMI'''] = '''    p[0] = None'''
actions['''exprsuite_star : exprsuite_star SEMI'''] = '''    p[0] = None'''
actions['''exprsuite_star2 : SEMI'''] = '''    p[0] = None'''
actions['''exprsuite_star2 : exprsuite_star2 SEMI'''] = '''    p[0] = None'''
actions['''closed_exprsuite : LBRACE closed_exprsuite_star suite RBRACE'''] = '''    p[0] = p[3]'''
actions['''closed_exprsuite : COLON LBRACE closed_exprsuite_star2 suite RBRACE'''] = '''    p[0] = p[4]'''
actions['''closed_exprsuite_star : SEMI'''] = '''    p[0] = None'''
actions['''closed_exprsuite_star : closed_exprsuite_star SEMI'''] = '''    p[0] = None'''
actions['''closed_exprsuite_star2 : SEMI'''] = '''    p[0] = None'''
actions['''closed_exprsuite_star2 : closed_exprsuite_star2 SEMI'''] = '''    p[0] = None'''
