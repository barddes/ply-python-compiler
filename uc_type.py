class uCType(object):
    '''
    Class that represents a type in the uC language.  Types
    are declared as singleton instances of this type.
    '''
    def __init__(self, typename, binary_ops=set(), unary_ops=set(), rel_ops=set(), assign_ops=set()):
        self.typename = typename
        self.unary_ops = unary_ops or set()
        self.binary_ops = binary_ops or set()
        self.rel_ops = rel_ops or set()
        self.assign_ops = assign_ops or set()

IntType = uCType("int",
    unary_ops   = {"-", "+", "--", "++", "p--", "p++", "*", "&"},
    binary_ops  = {"+", "-", "*", "/", "%"},
    rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
    assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="}
                 )

FloatType = uCType("float",
    unary_ops   = {"-", "+", "*", "&"},
    binary_ops  = {"+", "-", "*", "/", "%"},
    rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
    assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="}
                 )

CharType = uCType("char",
    unary_ops   = {"*", "&"},
    rel_ops     = {"==", "!=", "&&", "||"},
                  )


BoolType = uCType("bool",
    unary_ops   = { "!", "*", "&"},
    rel_ops     = {"==", "!=", "&&", "||"},
                  )


ArrayType = uCType("array",
    unary_ops   = {"*", "&"},
    rel_ops     = {"==", "!="}
                   )

StringType = uCType("string",
    unary_ops   = {},
    rel_ops     = {"==", "!="}
                   )

PtrType = uCType("ptr",
    unary_ops   = {"*", "&"},
    rel_ops     = {"==", "!="}
                   )

VoidType = uCType("void",
    unary_ops   = {"*", "&"},
    binary_ops     = {}
                   )