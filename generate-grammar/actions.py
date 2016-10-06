#!/usr/bin/env python

# Literally copied from Python's grammar: verified to produce the same AST and line numbers as Python 2.7.
actions = {}
actions['''or_test : and_test'''] = '''    p[0] = p[1]'''
actions['''or_test : and_test or_test_star'''] = '''    theor = Or()
    inherit_lineno(theor, p[2][0])
    p[0] = BoolOp(theor, [p[1]] + p[2], )
    inherit_lineno(p[0], p[1])'''
actions['''or_test_star : OR and_test'''] = '''    p[0] = [p[2]]'''
actions['''or_test_star : or_test_star OR and_test'''] = '''    p[0] = p[1] + [p[3]]'''
actions['''and_test : not_test'''] = '''    p[0] = p[1]'''
actions['''and_test : not_test and_test_star'''] = '''    theand = And()
    inherit_lineno(theand, p[2][0])
    p[0] = BoolOp(theand, [p[1]] + p[2], )
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
    p[0] = UnaryOp(op, p[2], )
    inherit_lineno(p[0], op)'''
actions['''factor : MINUS factor'''] = '''    if isinstance(p[2], Num) and not hasattr(p[2], "unary"):
        p[2].n *= -1
        p[0] = p[2]
        p[0].unary = True
        inherit_lineno(p[0], p[1][1])
    else:
        op = USub(**p[1][1])
        p[0] = UnaryOp(op, p[2], )
        inherit_lineno(p[0], op)'''
actions['''factor : power'''] = '''    p[0] = p[1]'''
actions['''power : atom'''] = '''    p[0] = p[1]'''
actions['''power : atom DOUBLESTAR factor'''] = '''    p[0] = BinOp(p[1], Pow(**p[2][1]), p[3], )
    inherit_lineno(p[0], p[1])'''
actions['''power : atom power_star'''] = '''    p[0] = unpack_trailer(p[1], p[2])'''
actions['''power : atom power_star DOUBLESTAR factor'''] = '''    p[0] = BinOp(unpack_trailer(p[1], p[2]), Pow(**p[3][1]), p[4], )
    inherit_lineno(p[0], p[1])'''
actions['''power_star : trailer'''] = '''    p[0] = [p[1]]'''
actions['''power_star : power_star trailer'''] = '''    p[0] = p[1] + [p[2]]'''
actions['''trailer : LPAR arglist RPAR'''] = '''    p[0] = p[2]'''
actions['''trailer : LSQB subscriptlist RSQB'''] = '''    p[0] = Subscript(None, p[2], Load(), )'''
actions['''trailer : DOT NAME'''] = '''    p[0] = Attribute(None, p[2][0], Load(), )'''
actions['''subscriptlist : subscript'''] = '''    p[0] = p[1]'''
actions['''subscriptlist : subscript COMMA'''] = '''    if isinstance(p[1], Index):
        tup = Tuple([p[1].value], Load(), paren=False)
        inherit_lineno(tup, p[1].value)
        p[0] = Index(tup, )
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice([p[1]], )
        inherit_lineno(p[0], p[1])'''
actions['''subscriptlist : subscript subscriptlist_star'''] = '''    args = [p[1]] + p[2]
    if all(isinstance(x, Index) for x in args):
        tup = Tuple([x.value for x in args], Load(), paren=False)
        inherit_lineno(tup, args[0].value)
        p[0] = Index(tup, )
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice(args, )
        inherit_lineno(p[0], p[1])'''
actions['''subscriptlist : subscript subscriptlist_star COMMA'''] = '''    args = [p[1]] + p[2]
    if all(isinstance(x, Index) for x in args):
        tup = Tuple([x.value for x in args], Load(), paren=False)
        inherit_lineno(tup, args[0].value)
        p[0] = Index(tup, )
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice(args, )
        inherit_lineno(p[0], p[1])'''
actions['''subscriptlist_star : COMMA subscript'''] = '''    p[0] = [p[2]]'''
actions['''subscriptlist_star : subscriptlist_star COMMA subscript'''] = '''    p[0] = p[1] + [p[3]]'''
actions['''subscript : COLON'''] = '''    p[0] = Slice(None, None, None, **p[1][1])'''
actions['''subscript : COLON sliceop'''] = '''    p[0] = Slice(None, None, p[2], **p[1][1])'''
actions['''sliceop : COLON'''] = '''    p[0] = Name("None", Load(), **p[1][1])'''
