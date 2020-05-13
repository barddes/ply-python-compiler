class uCType(object):
    '''
    Class that represents a type in the uC language.  Types
    are declared as singleton instances of this type.
    '''

    def __init__(self, typename, binary_ops=None, unary_ops=None, rel_ops=None, assign_ops=None):
        self.typename = typename
        self.unary_ops = unary_ops if unary_ops else set()
        self.binary_ops = binary_ops if binary_ops else set()
        self.rel_ops = rel_ops if rel_ops else set()
        self.assign_ops = assign_ops if assign_ops else set()

    def __eq__(self, other):
        if self.typename == 'any' or other.typename == 'any':
            return True

        if self and other:
            return self.typename == other.typename
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.typename

    def __repr__(self):
        return self.typename


EmptyType = uCType(None)

AnyType = uCType('any',
                 unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops={"+", "-", "*", "/", "%"},
                 rel_ops={"==", "!=", "<", ">", "<=", ">=", "&&", "||"},
                 assign_ops={"=", "+=", "-=", "*=", "/=", "%="}
                 )

IntType = uCType("int",
                 unary_ops={"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops={"+", "-", "*", "/", "%"},
                 rel_ops={"==", "!=", "<", ">", "<=", ">="},
                 assign_ops={"=", "+=", "-=", "*=", "/=", "%="}
                 )

FloatType = uCType("float",
                   unary_ops={"-", "+", "*", "&"},
                   binary_ops={"+", "-", "*", "/", "%"},
                   rel_ops={"==", "!=", "<", ">", "<=", ">="},
                   assign_ops={"=", "+=", "-=", "*=", "/=", "%="}
                   )

CharType = uCType("char",
                  unary_ops={"*", "&"},
                  rel_ops={"==", "!=", "&&", "||"},
                  )

ArrayType = uCType("array",
                   unary_ops={"*", "&"},
                   rel_ops={"==", "!="}
                   )

StringType = uCType("string",
                    unary_ops={},
                    binary_ops={"+"},
                    rel_ops={"==", "!="}
                    )

PtrType = uCType("ptr",
                 unary_ops={"*", "&"},
                 rel_ops={"==", "!="}
                 )

VoidType = uCType("void",
                  unary_ops={"*", "&"},
                  binary_ops={}
                  )

FuncType = uCType("func")
