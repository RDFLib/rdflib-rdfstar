
import re
import lark
import hashlib

from lark import (
    Lark,
    Transformer,
    Tree,
)
from lark.visitors import Visitor
from lark.reconstruct import Reconstructor

from lark.lexer import (
    Token,
)

from pymantic.compat import (
    binary_type,
)
from pymantic.parsers.base import (
    BaseParser,
)
from pymantic.primitives import (
    BlankNode,
    Literal,
    NamedNode,
    Triple,
)
from pymantic.util import (
    grouper,
    smart_urljoin,
    decode_literal,
)

grammar = r"""ntriplesdoc: statement*
?statement: directive | triples "." | quotedtriples "."
directive: prefix_id | base | sparql_prefix | sparql_base
prefix_id: "@prefix" PNAME_NS IRIREF "."
base: BASE_DIRECTIVE IRIREF "."
sparql_base: /BASE/i IRIREF
sparql_prefix: /PREFIX/i PNAME_NS IRIREF
triples: subject predicate_object_list
       | blank_node_property_list predicate_object_list?
insidequotation: qtsubject verb qtobject
quotedtriples: triples compoundanno
predicate_object_list: verb object_list (";" (verb object_list)?)*
?object_list: object ("," object)*
?verb: predicate | /a/
?subject: iri | blank_node | collection | quotation
?predicate: iri
?object: iri | blank_node | collection | blank_node_property_list | literal | quotation
?literal: rdf_literal | numeric_literal | boolean_literal
?qtsubject: iri | blank_node | quotation
?qtobject: 	iri | blank_node | literal | quotation
quotation: "<<" insidequotation ">>"
COMPOUNDL: "{|"
COMPOUNDR: "|}"
compoundanno: COMPOUNDL predicate_object_list COMPOUNDR
blank_node_property_list: "[" predicate_object_list "]"
collection: "(" object* ")"
numeric_literal: INTEGER | DECIMAL | DOUBLE
rdf_literal: string (LANGTAG | "^^" iri)?
boolean_literal: /true|false/
string: STRING_LITERAL_QUOTE
      | STRING_LITERAL_SINGLE_QUOTE
      | STRING_LITERAL_LONG_SINGLE_QUOTE
      | STRING_LITERAL_LONG_QUOTE
iri: IRIREF | prefixed_name
prefixed_name: PNAME_LN | PNAME_NS
blank_node: BLANK_NODE_LABEL | ANON

BASE_DIRECTIVE: "@base"
IRIREF: "<" (/[^\x00-\x20<>"{}|^`\\]/ | UCHAR)* ">"
PNAME_NS: PN_PREFIX? ":"
PNAME_LN: PNAME_NS PN_LOCAL
BLANK_NODE_LABEL: "_:" (PN_CHARS_U | /[0-9]/) ((PN_CHARS | ".")* PN_CHARS)?
LANGTAG: "@" /[a-zA-Z]+/ ("-" /[a-zA-Z0-9]+/)*
INTEGER: /[+-]?[0-9]+/
DECIMAL: /[+-]?[0-9]*/ "." /[0-9]+/
DOUBLE: /[+-]?/ (/[0-9]+/ "." /[0-9]*/ EXPONENT
      | "." /[0-9]+/ EXPONENT | /[0-9]+/ EXPONENT)
EXPONENT: /[eE][+-]?[0-9]+/
STRING_LITERAL_QUOTE: "\"" (/[^\x22\x5C\x0A\x0D]/ | ECHAR | UCHAR)* "\""
STRING_LITERAL_SINGLE_QUOTE: "'" (/[^\x27\x5C\x0A\x0D]/ | ECHAR | UCHAR)* "'"
STRING_LITERAL_LONG_SINGLE_QUOTE: "'''" (/'|''/? (/[^'\\]/ | ECHAR | UCHAR))* "'''"
STRING_LITERAL_LONG_QUOTE: "\"\"\"" (/"|""/? (/[^"\\]/ | ECHAR | UCHAR))* "\"\"\""
UCHAR: "\\u" HEX~4 | "\\U" HEX~8
ECHAR: "\\" /[tbnrf"'\\]/
WS: /[\x20\x09\x0D\x0A]/
ANON: "[" WS* "]"
PN_CHARS_BASE: /[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF]/
PN_CHARS_U: PN_CHARS_BASE | "_"
PN_CHARS: PN_CHARS_U | /[\-0-9\u00B7\u0300-\u036F\u203F-\u2040]/
PN_PREFIX: PN_CHARS_BASE ((PN_CHARS | ".")* PN_CHARS)?
PN_LOCAL: (PN_CHARS_U | ":" | /[0-9]/ | PLX) ((PN_CHARS | "." | ":" | PLX)* (PN_CHARS | ":" | PLX))?
PLX: PERCENT | PN_LOCAL_ESC
PERCENT: "%" HEX~2
HEX: /[0-9A-Fa-f]/
PN_LOCAL_ESC: "\\" /[_~\.\-!$&'()*+,;=\/?#@%]/

%ignore WS
COMMENT: "#" /[^\n]/*
%ignore COMMENT
"""

# r"""ntriplesdoc: statement*
# ?statement: triples "." | triples "."? (EOL triples ".")* EOL?
# triples: subject predicate object
# ?verb: predicate | /a/
# ?subject: IRIREF | BLANK_NODE_LABEL | quotation
# ?predicate: IRIREF
# ?object: IRIREF | BLANK_NODE_LABEL | literal | quotation
# ?literal: rdf_literal | numeric_literal | boolean_literal
# ANGLEBRACKETL: "<<"
# ANGLEBRACKETR: ">>"
# quotation: ANGLEBRACKETL triples ANGLEBRACKETR
# numeric_literal: INTEGER | DECIMAL | DOUBLE
# rdf_literal: string (LANGTAG | "^^" iri)?
# boolean_literal: /true|false/
# string: STRING_LITERAL_QUOTE
#       | STRING_LITERAL_SINGLE_QUOTE
#       | STRING_LITERAL_LONG_SINGLE_QUOTE
#       | STRING_LITERAL_LONG_QUOTE
# iri: IRIREF | prefixed_name
# prefixed_name: PNAME_LN | PNAME_NS

# EOL: /[#xD#xA]+/
# IRIREF: "<" (/[^\x00-\x20<>"{}|^`\\]/ | UCHAR)* ">"
# PNAME_NS: PN_PREFIX? ":"
# PNAME_LN: PNAME_NS PN_LOCAL
# BLANK_NODE_LABEL: "_:" (PN_CHARS_U | /[0-9]/) ((PN_CHARS | ".")* PN_CHARS)?
# LANGTAG: "@" /[a-zA-Z]+/ ("-" /[a-zA-Z0-9]+/)*
# INTEGER: /[+-]?[0-9]+/
# DECIMAL: /[+-]?[0-9]*/ "." /[0-9]+/
# DOUBLE: /[+-]?/ (/[0-9]+/ "." /[0-9]*/ EXPONENT
#       | "." /[0-9]+/ EXPONENT | /[0-9]+/ EXPONENT)
# EXPONENT: /[eE][+-]?[0-9]+/
# STRING_LITERAL_QUOTE: "\"" (/[^\x22\x5C\x0A\x0D]/ | ECHAR | UCHAR)* "\""
# STRING_LITERAL_SINGLE_QUOTE: "'" (/[^\x27\x5C\x0A\x0D]/ | ECHAR | UCHAR)* "'"
# STRING_LITERAL_LONG_SINGLE_QUOTE: "'''" (/'|''/? (/[^'\\]/ | ECHAR | UCHAR))* "'''"
# STRING_LITERAL_LONG_QUOTE: "\"\"\"" (/"|""/? (/[^"\\]/ | ECHAR | UCHAR))* "\"\"\""
# UCHAR: "\\u" HEX~4 | "\\U" HEX~8
# ECHAR: "\\" /[tbnrf"'\\]/
# WS: /[\x20\x09\x0D\x0A]/
# ANON: "[" WS* "]"
# PN_CHARS_BASE: /[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF]/
# PN_CHARS_U: PN_CHARS_BASE | "_"
# PN_CHARS: PN_CHARS_U | /[\-0-9\u00B7\u0300-\u036F\u203F-\u2040]/
# PN_PREFIX: PN_CHARS_BASE ((PN_CHARS | ".")* PN_CHARS)?
# PN_LOCAL: (PN_CHARS_U | ":" | /[0-9]/ | PLX) ((PN_CHARS | "." | ":" | PLX)* (PN_CHARS | ":" | PLX))?
# PLX: PERCENT | PN_LOCAL_ESC
# PERCENT: "%" HEX~2
# HEX: /[0-9A-Fa-f]/
# PN_LOCAL_ESC: "\\" /[_~\.\-!$&'()*+,;=\/?#@%]/

# %ignore WS
# COMMENT: "#" /[^\n]/*
# %ignore COMMENT
# """

ntriples_lark = Lark(grammar, start="ntriplesdoc", parser="lalr", maybe_placeholders = False)

f = open("ntriples-star/ntriples-star-syntax-1.nt", "rb")
rdbytes = f.read()
f.close()
rdbytes_processing = rdbytes.decode("utf-8")

class Print_Tree(Visitor):
    def print_quotation(self, tree):
        assert tree.data == "quotation"
        print(tree.children)

tree = ntriples_lark.parse(rdbytes_processing)
print(tree)
print("\n")
print("\n")
print("\n")
print("\n")
print("\n")
print("\n")
print("\n")
print("\n")

from lark import Visitor, v_args
quotation_list = []
quotation_dict = dict()
vblist = []
quotationreif = []
prefix_list = []
quotationannolist = []
quoted_or_not = False
both_quoted_and_asserted = False
assertedtriplelist = []

def myHash(text:str):
  return str(hashlib.md5(text.encode('utf-8')).hexdigest())

class FindVariables(Visitor):
    def __init__(self):
        super().__init__()
        # self.quotation_list = []
        self.variable_list = []

    def quotation(self, var):

        qut = Reconstructor(ntriples_lark).reconstruct(var) # replace here or replace later
        print("qqqqqqqqqqqqqqqqqqqqqqqqqqq", qut,"\n" )
        qut = qut.replace(";", "") #####################
        # qut = qut.replace(" ", "") #qut = qut.strip()
        if not (qut in quotation_list):
            quotation_list.append(qut)

        vr = Reconstructor(ntriples_lark).reconstruct(var)
        vr = vr.replace(";","")
        # vr = vr.replace(" ","")
        quotation_dict[qut] = str(myHash(qut))
        qut_hash = ":" + str(myHash(qut))
        # try:
        id = quotation_dict.get(vr)
        for x in quotation_dict:
            if x in vr:
                # print("replace", x, ":"+quotation_dict.get(x))
                vr = vr.replace(x, ":"+quotation_dict.get(x))
                vr = vr.replace("<<", "")
                vr = vr.replace(">>", "")
                output = vr.split(":") # what if not :? directly url? if and else?
                output.pop(0)
                oa1 = Reconstructor(ntriples_lark).reconstruct(var)
                oa1 = oa1.replace(";","")
                # oa1 = oa1.replace(" ","")
                output.append(oa1)
                # print(quotationreif)
                if (not (output in quotationreif)):
                    quotationreif.append(output)

        # print("fixing quotation before",var)
        # var = Tree('iri', [Tree('prefixed_name', [Token('PNAME_LN', qut_hash)])])
        # print("fixing quotation",var)

        ##################
        #########################

    def insidequotation(self, var):
        appends1 = []
        for x in var.children:
            x1 = Reconstructor(ntriples_lark).reconstruct(x)
            x1 = x1.replace(";","")
            # x1 = x1.replace(" ","")
            appends1.append(x1)

        if not (appends1 in vblist):
            vblist.append(appends1)

    def triples(self, var):

        appends1 = []
        tri = Reconstructor(ntriples_lark).reconstruct(var)
        print("ttttttttttttttttttttttttttttt", tri,"\n" )
        tri = tri.replace(";", "")
        if not (tri in assertedtriplelist):
            assertedtriplelist.append(tri)
        for x in var.children:
            # print(x.data)
            if x.data == 'predicate_object_list':
                xc = x.children
                for y in xc:
                    x2 = Reconstructor(ntriples_lark).reconstruct(y)
                    x2 = x2.replace(";","")
                    # x2 = x2.replace(" ","")
                    appends1.append(x2) # or push
            else:
              print("how to edit2", x)
              anyquotationin = False
              x1 = Reconstructor(ntriples_lark).reconstruct(x)
              x1 = x1.replace(";","")
            #   x1 = x1.replace(" ","")
              print("compareed", x1)
              appends1.append(x1)

        if not (appends1 in vblist):
            vblist.append(appends1)

at = FindVariables().visit(tree)
print("what is in the quotation: ", quotation_list, "\nwhat quotations need to represent: ", quotationreif, "\nwhat are the original lists of statements: ", vblist, "\nwhat are the quotation_dict: ", quotation_dict)
print("\n compound", quotationannolist)
constructors = ""

for y in vblist:
    # print("warc3casca", y)
    for element_index in range(0, len(y)):
        if (y[element_index][0] == "_") & (not (element_index == 0)):
            y[element_index]=" "+y[element_index]
    result = "".join(y)
    if result in assertedtriplelist:
        print("testassertedtriplelist", result)
        test1 = "<<"+result+">>"
        if test1 in quotation_list:
            both_quoted_and_asserted = True
        else:
            both_quoted_and_asserted = False
            quoted_or_not = False
    else:
        print("testassertedtriplelist2", result)
        test2 = "<<"+result+">>"
        if test2 in quotation_list:
            both_quoted_and_asserted = False
            quoted_or_not = True
        else:
            both_quoted_and_asserted = False
            quoted_or_not = False
    result = "<<"+result+">>"
    # print("fixing bnode", result)
    if not (result in quotation_list):
        for z in range(0,len(y)):
            if "<<" in y[z]:
                y[z] = "_:"+quotation_dict[y[z]]
        myvalue = str(myHash(result))
        # print("asrtrrrrrtt", myvalue)
        subject = y[0]
        predicate = y[1]
        object = y[2]
        if both_quoted_and_asserted:
            next_rdf_object = "_:" + str(myvalue) + '\n' + "    a rdfstar:AssertedStatement, rdfstar:QuotedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
        else:
            if quoted_or_not:
                next_rdf_object = "_:" + str(myvalue) + '\n' + "    a rdfstar:QuotedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
            else:
                next_rdf_object = "_:" + str(myvalue) + '\n' + "    a rdfstar:AssertedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
        constructors+=next_rdf_object
    else:
        value = quotation_dict[result]
        for z in range(0,len(y)):
            if "<<" in y[z]:
                y[z] = "_:"+quotation_dict[y[z]]
        subject = y[0]
        predicate = y[1]
        object = y[2]
        if both_quoted_and_asserted:
            next_rdf_object = "_:" + str(value) + '\n' + "    a rdfstar:AssertedStatement, rdfstar:QuotedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
        else:
            if quoted_or_not:
                next_rdf_object = "_:" + str(value) + '\n' + "    a rdfstar:QuotedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
            else:
                next_rdf_object = "_:" + str(value) + '\n' + "    a rdfstar:AssertedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
        constructors+=next_rdf_object

for z in quotationannolist:
    result1 = "".join(z)
    result1 = "<<"+result1+">>"
    value = str(myHash(result1))
    subject = z[0]
    predicate = z[1]
    object = z[2]
    next_rdf_object = "_:" + str(value) + '\n' + "    a rdf:Statement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
    constructors+=next_rdf_object

for x in range(0, len(prefix_list)):
    prefix_list[x] = Reconstructor(ntriples_lark).reconstruct(prefix_list[x])
    constructors = prefix_list[x]+"\n"+constructors

constructors = "PREFIX rdfstar: <https://w3id.org/rdf-star/> \n"+constructors

constructors = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \n"+constructors

# constructors = "PREFIX : <http://example/> \n"+constructors # prefix

if not (("PREFIX : <http://example/>" in constructors) or ("PREFIX:<http://example/>" in constructors)):
    constructors = "PREFIX : <http://example/> \n"+constructors

if "PREFIX:" in constructors:
    constructors = constructors.replace("PREFIX:", "PREFIX :")


print(constructors)
# if len x in quotatioinreif ==2 3.................
# string +=
# string = ...........

# :rei-1
#a rdf:Statement ;
#rdf:subject :s ;
#rdf:predicate :p ;
#rdf:object :o ;
#.

# fv2 = fv.visit(tree)
# print(fv)
# for var in fv.variable_list:
#     print(var)
#     print("\n")
#     print("\n")
#     print("\n")
#     print("\n")
#     print("\n")

#################################################

# RDF_TYPE = NamedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
# RDF_NIL = NamedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#nil')
# RDF_FIRST = NamedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#first')
# RDF_REST = NamedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#rest')

# XSD_DECIMAL = NamedNode('http://www.w3.org/2001/XMLSchema#decimal')
# XSD_DOUBLE = NamedNode('http://www.w3.org/2001/XMLSchema#double')
# XSD_INTEGER = NamedNode('http://www.w3.org/2001/XMLSchema#integer')
# XSD_BOOLEAN = NamedNode('http://www.w3.org/2001/XMLSchema#boolean')
# XSD_STRING = NamedNode('http://www.w3.org/2001/XMLSchema#string')

# LEGAL_IRI = re.compile(r'^[^\x00-\x20<>"{}|^`\\]*$')


# def validate_iri(iri):
#     if not LEGAL_IRI.match(iri):
#         raise ValueError('Illegal characters in IRI: ' + iri)
#     return iri

# def unpack_predicate_object_list(subject, pol):
#     if not isinstance(subject, (NamedNode, BlankNode)):
#         for triple_or_node in subject:
#             if isinstance(triple_or_node, Triple):
#                 yield triple_or_node
#             else:
#                 subject = triple_or_node
#                 break

#     for predicate, object_ in grouper(pol, 2):
#         if isinstance(predicate, Token):
#             if predicate.value != 'a':
#                 raise ValueError(predicate)
#             predicate = RDF_TYPE

#         if not isinstance(object_, (NamedNode, Literal, BlankNode)):
#             if isinstance(object_, Tree):
#                 object_ = object_.children
#             for triple_or_node in object_:
#                 if isinstance(triple_or_node, Triple):
#                     yield triple_or_node
#                 else:
#                     object_ = triple_or_node
#                     yield Triple(subject, predicate, object_)
#         else:
#             yield Triple(subject, predicate, object_)

# class TurtleTransformer(Transformer, BaseParser):
#     def __init__(self, base_iri=''):
#         super(TurtleTransformer, self).__init__()
#         self.base_iri = base_iri
#         self.prefixes = self.profile.prefixes

#     def decode_iriref(self, iriref):
#         return validate_iri(decode_literal(iriref[1:-1]))


#     def iri(self, children):
#         iriref_or_pname, = children

#         if iriref_or_pname.startswith('<'):
#             return self.make_named_node(smart_urljoin(
#                 self.base_iri, self.decode_iriref(iriref_or_pname)))

#         return iriref_or_pname


#     def predicate_object_list(self, children):
#         return children


#     def triples(self, children):
#         if len(children) == 2:
#             subject = children[0]
#             for triple in unpack_predicate_object_list(subject, children[1]):
#                 yield triple
#         elif len(children) == 1:
#             for triple_or_node in children[0]:
#                 if isinstance(triple_or_node, Triple):
#                     yield triple_or_node


#     def prefixed_name(self, children):
#         pname, = children
#         ns, _, ln = pname.partition(':')
#         return self.make_named_node(self.prefixes[ns] + decode_literal(ln))


#     def prefix_id(self, children):
#         ns, iriref = children
#         iri = smart_urljoin(self.base_iri, self.decode_iriref(iriref))
#         ns = ns[:-1]  # Drop trailing : from namespace
#         self.prefixes[ns] = iri

#         return []


#     def sparql_prefix(self, children):
#         return self.prefix_id(children[1:])


#     def base(self, children):
#         base_directive, base_iriref = children

#         # Workaround for lalr parser token ambiguity in python 2.7
#         if base_directive.startswith('@') and base_directive != '@base':
#             raise ValueError('Unexpected @base: ' + base_directive)

#         self.base_iri = smart_urljoin(
#             self.base_iri, self.decode_iriref(base_iriref))

#         return []


#     def sparql_base(self, children):
#         return self.base(children)


#     def blank_node(self, children):
#         bn, = children

#         if bn.type == 'ANON':
#             return self.make_blank_node()
#         elif bn.type == 'BLANK_NODE_LABEL':
#             return self.make_blank_node(bn.value)
#         else:
#             raise NotImplementedError()


#     def blank_node_property_list(self, children):
#         pl_root = self.make_blank_node()
#         for pl_item in unpack_predicate_object_list(pl_root, children[0]):
#             yield pl_item
#         yield pl_root


#     def collection(self, children):
#         prev_node = RDF_NIL
#         for value in reversed(children):
#             this_bn = self.make_blank_node()
#             if not isinstance(value, (NamedNode, Literal, BlankNode)):
#                 for triple_or_node in value:
#                     if isinstance(triple_or_node, Triple):
#                         yield triple_or_node
#                     else:
#                         value = triple_or_node
#                         break
#             yield self.make_triple(this_bn, RDF_FIRST, value)
#             yield self.make_triple(this_bn, RDF_REST, prev_node)
#             prev_node = this_bn

#         yield prev_node


#     def numeric_literal(self, children):
#         numeric, = children

#         if numeric.type == 'DECIMAL':
#             return self.make_datatype_literal(numeric, datatype=XSD_DECIMAL)
#         elif numeric.type == 'DOUBLE':
#             return self.make_datatype_literal(numeric, datatype=XSD_DOUBLE)
#         elif numeric.type == 'INTEGER':
#             return self.make_datatype_literal(numeric, datatype=XSD_INTEGER)
#         else:
#             raise NotImplementedError()


#     def rdf_literal(self, children):
#         literal_string = children[0]
#         lang = None
#         type_ = None

#         if len(children) == 2 and isinstance(children[1], NamedNode):
#             type_ = children[1]
#             return self.make_datatype_literal(literal_string, type_)
#         elif len(children) == 2 and children[1].type == 'LANGTAG':
#             lang = children[1][1:]  # Remove @
#             return self.make_language_literal(literal_string, lang)
#         else:
#             return self.make_datatype_literal(
#                 literal_string, datatype=XSD_STRING)


#     def boolean_literal(self, children):
#         boolean, = children
#         return self.make_datatype_literal(boolean, datatype=XSD_BOOLEAN)


#     def string(self, children):
#         literal, = children
#         if literal.type in (
#             'STRING_LITERAL_QUOTE', 'STRING_LITERAL_SINGLE_QUOTE',
#         ):
#             string = decode_literal(literal[1:-1])
#         if literal.type in (
#             'STRING_LITERAL_LONG_SINGLE_QUOTE',
#             'STRING_LITERAL_LONG_QUOTE',
#         ):
#             string = decode_literal(literal[3:-3])

#         return string


#     def turtle_doc(self, children):
#         for child in children:
#             if not isinstance(child, Tree):
#                 for triple in child:
#                     yield triple

# tree2 = ntriples_lark.parse(rdbytes_processing)

# base=''
# tr = TurtleTransformer(base_iri=base)
# result = tr.transform(tree2)
# print(result)
