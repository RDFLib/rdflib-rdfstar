import pytest

from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from rdflib.exceptions import ParserError

from rdflib import Graph
from rdflib.util import guess_format


from rdflib.plugin import register
from rdflib.parser import Parser
from rdflib.serializer import Serializer

import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF
from rdflib.namespace import FOAF

register(
    "ttls",
    Parser,
    "rdflib.plugins.parsers.turtlestar",
    "TurtleParser",
)

register(
    "ttlstar",
    Serializer,
    "rdflib.plugins.serializers.turtlestar",
    "TurtlestarSerializer"
)

g = Graph()
g.parse(data="test/sparql-star/data-1.ttl", format = "ttls")
# q = "SELECT * { <<:a :b :c>> ?p ?o }"

f = open("test/sparql-star/sparql-star-basic-2-data-1-reified.rq", "rb")
sparqlbytes = f.read()
f.close()
sparqlbytes_processing = sparqlbytes.decode("utf-8")

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

# from pymantic.compat import (
#     binary_type,
# )
# from pymantic.parsers.base import (
#     BaseParser,
# )
# from pymantic.primitives import (
#     blanknode,
#     Literal,
#     NamedNode,
#     Triple,
# )
# from pymantic.util import (
#     grouper,
#     smart_urljoin,
#     decode_literal,
# )

grammar = r"""queryunit: query
query: prologue ( selectquery | constructquery | describequery | askquery ) valuesclause
updateunit	  :  	update
prologue	  :  	( basedecl | prefixdecl )*
basedecl	  :  	"BASE" IRIREF
prefixdecl	  :  	"PREFIX" PNAME_NS IRIREF
selectquery	  :  	selectclause datasetclause* whereclause solutionmodifier
subselect	  :  	selectclause whereclause solutionmodifier valuesclause
selectclause	  :  	"SELECT" ( "DISTINCT" | "REDUCED" )? ( ( var | ( "(" expression "AS" var ")" ) )+ | "*" )
constructquery	  :  	"CONSTRUCT" ( constructtemplate datasetclause* whereclause solutionmodifier | datasetclause* "WHERE" "{" triplestemplate? "}" solutionmodifier )
describequery	  :  	"DESCRIBE" ( varoriri+ | "*" ) datasetclause* whereclause? solutionmodifier
askquery	  :  	"ASK" datasetclause* whereclause solutionmodifier
datasetclause	  :  	"FROM" ( defaultgraphclause | namedgraphclause )
defaultgraphclause	  :  	sourceselector
namedgraphclause	  :  	"NAMED" sourceselector
sourceselector	  :  	iri
whereclause	  :  	"WHERE"? groupgraphpattern
solutionmodifier	  :  	groupclause? havingclause? orderclause? limitoffsetclauses?
groupclause	  :  	"GROUP" "BY" groupcondition+
groupcondition	  :  	builtincall | functioncall | "(" expression ( "AS" var )? ")" | var
havingclause	  :  	"HAVING" havingcondition+
havingcondition	  :  	constraint
orderclause	  :  	"ORDER" "BY" ordercondition+
ordercondition	  :  	( ( "ASC" | "DESC" ) brackettedexpression )
| ( constraint | var )
limitoffsetclauses	  :  	limitclause offsetclause? | offsetclause limitclause?
limitclause	  :  	"LIMIT" integer
offsetclause	  :  	"OFFSET" integer
valuesclause	  :  	( "VALUES" datablock )?
update	  :  	prologue ( update1 ( ";" update )? )?
update1	  :  	load | clear | drop | add | move | copy | create | insertdata | deletedata | deletewhere | modify
load	  :  	"load" "SILENT"? iri ( "INTO" graphref )?
clear	  :  	"clear" "SILENT"? graphrefall
drop	  :  	"drop" "SILENT"? graphrefall
create	  :  	"create" "SILENT"? graphref
add	  :  	"add" "SILENT"? graphordefault "TO" graphordefault
move	  :  	"move" "SILENT"? graphordefault "TO" graphordefault
copy	  :  	"copy" "SILENT"? graphordefault "TO" graphordefault
insertdata	  :  	"INSERT DATA" quaddata
deletedata	  :  	"DELETE DATA" quaddata
deletewhere	  :  	"DELETE WHERE" quadpattern
modify	  :  	( "WITH" iri )? ( deleteclause insertclause? | insertclause ) usingclause* "WHERE" groupgraphpattern
deleteclause	  :  	"DELETE" quadpattern
insertclause	  :  	"INSERT" quadpattern
usingclause	  :  	"USING" ( iri | "NAMED" iri )
graphordefault	  :  	"DEFAULT" | "GRAPH"? iri
graphref	  :  	"GRAPH" iri
graphrefall	  :  	graphref | "DEFAULT" | "NAMED" | "ALL"
quadpattern	  :  	"{" quads "}"
quaddata	  :  	"{" quads "}"
quads	  :  	triplestemplate? ( quadsnottriples "."? triplestemplate? )*
quadsnottriples	  :  	"GRAPH" varoriri "{" triplestemplate? "}"
triplestemplate	  :  	triplessamesubject ( "." triplestemplate? )?
groupgraphpattern	  :  	"{" ( subselect | groupgraphpatternsub ) "}"
groupgraphpatternsub	  :  	triplesblock? ( graphpatternnottriples "."? triplesblock? )*
triplesblock	  :  	triplessamesubjectpath ( "." triplesblock? )?
graphpatternnottriples	  :  	grouporuniongraphpattern | optionalgraphpattern | minusgraphpattern | graphgraphpattern | servicegraphpattern | filter | bind | inlinedata
optionalgraphpattern	  :  	"OPTIONAL" groupgraphpattern
graphgraphpattern	  :  	"GRAPH" varoriri groupgraphpattern
servicegraphpattern	  :  	"SERVICE" "SILENT"? varoriri groupgraphpattern
bind	  :  	"bind" "(" expression "AS" var ")"
inlinedata	  :  	"VALUES" datablock
datablock	  :  	inlinedataonevar | inlinedatafull
inlinedataonevar	  :  	var "{" datablockvalue* "}"
inlinedatafull	  :  	( NIL | "(" var* ")" ) "{" ( "(" datablockvalue* ")" | NIL )* "}"
datablockvalue	  :  	quotedtriple | iri | rdfliteral | numericliteral | booleanliteral | "UNDEF"
minusgraphpattern	  :  	"MINUS" groupgraphpattern
grouporuniongraphpattern	  :  	groupgraphpattern ( "UNION" groupgraphpattern )*
filter	  :  	"filter" constraint
constraint	  :  	brackettedexpression | builtincall | functioncall
functioncall	  :  	iri arglist
arglist	  :  	NIL | "(" "DISTINCT"? expression ( "," expression )* ")"
expressionlist	  :  	NIL | "(" expression ( "," expression )* ")"
constructtemplate	  :  	"{" constructtriples? "}"
constructtriples	  :  	triplessamesubject ( "." constructtriples? )?
triplessamesubject	  :  	varortermorquotedtp propertylistnotempty | triplesnode propertylist
propertylist	  :  	propertylistnotempty?
propertylistnotempty	  :  	verb objectlist ( ";" ( verb objectlist )? )*
verb	  :  	varoriri | "a"
objectlist	  :  	object ( "," object )*
object	  :  	graphnode annotationpattern?
triplessamesubjectpath	  :  	varortermorquotedtp propertylistpathnotempty | triplesnodepath propertylistpath
propertylistpath	  :  	propertylistpathnotempty?
propertylistpathnotempty	  :  	( verbpath | verbsimple ) objectlistpath ( ";" ( ( verbpath | verbsimple ) objectlist )? )*
verbpath	  :  	path
verbsimple	  :  	var
objectlistpath	  :  	objectpath ( "," objectpath )*
objectpath	  :  	graphnodepath annotationpattern?
path	  :  	pathalternative
pathalternative	  :  	pathsequence ( "|" pathsequence )*
pathsequence	  :  	patheltorinverse ( "/" patheltorinverse )*
pathelt	  :  	pathprimary pathmod?
patheltorinverse	  :  	pathelt | "^" pathelt
pathmod	  :  	"?" | "*" | "+"
pathprimary	  :  	iri | "a" | "!" pathnegatedpropertyset | "(" path ")"
pathnegatedpropertyset	  :  	pathoneinpropertyset | "(" ( pathoneinpropertyset ( "|" pathoneinpropertyset )* )? ")"
pathoneinpropertyset	  :  	iri | "a" | "^" ( iri | "a" )
integer	  :  	INTEGER
triplesnode	  :  	collection | blanknodepropertylist
blanknodepropertylist	  :  	"[" propertylistnotempty "]"
triplesnodepath	  :  	collectionpath | blanknodepropertylistpath
blanknodepropertylistpath	  :  	"[" propertylistpathnotempty "]"
collection	  :  	"(" graphnode+ ")"
collectionpath	  :  	"(" graphnodepath+ ")"
graphnode	  :  	varortermorquotedtp | triplesnode
graphnodepath	  :  	varortermorquotedtp | triplesnodepath
varorterm	  :  	var | graphterm
varoriri	  :  	var | iri
var	  :  	var1 | var2
graphterm	  :  	iri | rdfliteral | numericliteral | booleanliteral | blanknode | NIL
expression	  :  	conditionalorexpression
conditionalorexpression	  :  	conditionalandexpression ( "||" conditionalandexpression )*
conditionalandexpression	  :  	valuelogical ( "&&" valuelogical )*
valuelogical	  :  	relationalexpression
relationalexpression	  :  	numericexpression ( "=" numericexpression | "!=" numericexpression | "<" numericexpression | ">" numericexpression | "<=" numericexpression | ">=" numericexpression | "IN" expressionlist | "NOT" "IN" expressionlist )?
numericexpression	  :  	additiveexpression
additiveexpression	  :  	multiplicativeexpression ( "+" multiplicativeexpression | "-" multiplicativeexpression | ( numericliteralpositive | numericliteralnegative ) ( ( "*" unaryexpression ) | ( "/" unaryexpression ) )* )*
multiplicativeexpression	  :  	unaryexpression ( "*" unaryexpression | "/" unaryexpression )*
unaryexpression	  :  	  "!" primaryexpression
| "+" primaryexpression
| "-" primaryexpression
| primaryexpression
primaryexpression	  :  	brackettedexpression | builtincall | iriorfunction | rdfliteral | numericliteral | booleanliteral | var | exprquotedtp
brackettedexpression	  :  	"(" expression ")"
builtincall	  :  	  aggregate
| "STR" "(" expression ")"
| "LANG" "(" expression ")"
| "LANGMATCHES" "(" expression "," expression ")"
| "DATATYPE" "(" expression ")"
| "BOUND" "(" var ")"
| "IRI" "(" expression ")"
| "URI" "(" expression ")"
| "BNODE" ( "(" expression ")" | NIL )
| "RAND" NIL
| "ABS" "(" expression ")"
| "CEIL" "(" expression ")"
| "FLOOR" "(" expression ")"
| "ROUND" "(" expression ")"
| "CONCAT" expressionlist
| substringexpression
| "STRLEN" "(" expression ")"
| strreplaceexpression
| "UCASE" "(" expression ")"
| "LCASE" "(" expression ")"
| "ENCODE_FOR_URI" "(" expression ")"
| "CONTAINS" "(" expression "," expression ")"
| "STRSTARTS" "(" expression "," expression ")"
| "STRENDS" "(" expression "," expression ")"
| "STRBEFORE" "(" expression "," expression ")"
| "STRAFTER" "(" expression "," expression ")"
| "YEAR" "(" expression ")"
| "MONTH" "(" expression ")"
| "DAY" "(" expression ")"
| "HOURS" "(" expression ")"
| "MINUTES" "(" expression ")"
| "SECONDS" "(" expression ")"
| "TIMEZONE" "(" expression ")"
| "TZ" "(" expression ")"
| "NOW" NIL
| "UUID" NIL
| "STRUUID" NIL
| "MD5" "(" expression ")"
| "SHA1" "(" expression ")"
| "SHA256" "(" expression ")"
| "SHA384" "(" expression ")"
| "SHA512" "(" expression ")"
| "COALESCE" expressionlist
| "IF" "(" expression "," expression "," expression ")"
| "STRLANG" "(" expression "," expression ")"
| "STRDT" "(" expression "," expression ")"
| "sameTerm" "(" expression "," expression ")"
| "isIRI" "(" expression ")"
| "isURI" "(" expression ")"
| "isBLANK" "(" expression ")"
| "isLITERAL" "(" expression ")"
| "isNUMERIC" "(" expression ")"
| regexexpression
| existsfunc
| notexistsfunc
| "TRIPLE" "(" expression "," expression "," expression ")"
| "SUBJECT" "(" expression ")"
| "PREDICATE" "(" expression ")"
| "OBJECT" "(" expression ")"
| "isTRIPLE" "(" expression ")"
quotedtp	: "<<" qtsubjectorobject verb qtsubjectorobject ">>"
quotedtriple	: "<<" datavalueterm ( iri | "a" ) datavalueterm ">>"
qtsubjectorobject	: var | blanknode | iri | rdfliteral | numericliteral | booleanliteral | quotedtp
datavalueterm	: iri | rdfliteral | numericliteral | booleanliteral | quotedtriple
varortermorquotedtp	: var | graphterm | quotedtp
annotationpattern	: "{|" propertylistnotempty "|}"
annotationpatternpath	: "{|" propertylistpathnotempty "|}"
exprquotedtp	: "<<" exprvarorterm verb exprvarorterm ">>"
exprvarorterm	: iri | rdfliteral | numericliteral | booleanliteral | var | exprquotedtp
regexexpression	  :  	"REGEX" "(" expression "," expression ( "," expression )? ")"
substringexpression	  :  	"SUBSTR" "(" expression "," expression ( "," expression )? ")"
strreplaceexpression	  :  	"REPLACE" "(" expression "," expression "," expression ( "," expression )? ")"
existsfunc	  :  	"EXISTS" groupgraphpattern
notexistsfunc	  :  	"NOT" "EXISTS" groupgraphpattern
aggregate	  :  	  "COUNT" "(" "DISTINCT"? ( "*" | expression ) ")"
| "SUM" "(" "DISTINCT"? expression ")"
| "MIN" "(" "DISTINCT"? expression ")"
| "MAX" "(" "DISTINCT"? expression ")"
| "AVG" "(" "DISTINCT"? expression ")"
| "SAMPLE" "(" "DISTINCT"? expression ")"
| "GROUP_CONCAT" "(" "DISTINCT"? expression ( ";" "SEPARATOR" "=" string )? ")"
iriorfunction	  :  	iri arglist?
rdfliteral	  :  	string ( LANGTAG | ( "^^" iri ) )?
numericliteral	  :  	numericliteralunsigned | numericliteralpositive | numericliteralnegative
numericliteralunsigned	  :  	INTEGER | DECIMAL | DOUBLE
numericliteralpositive	  :  	INTEGER_POSITIVE | DECIMAL_POSITIVE | DOUBLE_POSITIVE
numericliteralnegative	  :  	INTEGER_NEGATIVE | DECIMAL_NEGATIVE | DOUBLE_NEGATIVE
booleanliteral	  :  	"true" | "false"
string	  :  	STRING_LITERAL_QUOTE | STRING_LITERAL_SINGLE_QUOTE | STRING_LITERAL_LONG_QUOTE | STRING_LITERAL_LONG_SINGLE_QUOTE
iri	  :  	IRIREF | prefixedname
prefixedname	  :  	PNAME_LN | PNAME_NS
blanknode	  :  	BLANK_NODE_LABEL | ANON

BASE_DIRECTIVE: "@base"
var1	  : 	"?" varname
var2	  : 	"$" varname
varname	  : 	PN_CHARS
IRIREF: "<" (/[^\x00-\x20<>"{}|^`\\]/ | UCHAR)* ">"
PNAME_NS: PN_PREFIX? ":"
PNAME_LN: PNAME_NS PN_LOCAL
BLANK_NODE_LABEL: "_:" (PN_CHARS_U | /[0-9]/) ((PN_CHARS | ".")* PN_CHARS)?
LANGTAG: "@" /[a-zA-Z]+/ ("-" /[a-zA-Z0-9]+/)*
INTEGER: /[+-]?[0-9]+/
NIL	  :  	"(" WS* ")"
DECIMAL: /[+-]?[0-9]*/ "." /[0-9]+/
DOUBLE: /[+-]?/ (/[0-9]+/ "." /[0-9]*/ EXPONENT
      | "." /[0-9]+/ EXPONENT | /[0-9]+/ EXPONENT)
INTEGER_POSITIVE	  :  	"+" INTEGER
DECIMAL_POSITIVE	  :  	"+" DECIMAL
DOUBLE_POSITIVE	      :  	"+" DOUBLE
INTEGER_NEGATIVE	  :  	"-" INTEGER
DECIMAL_NEGATIVE	  :	    "-" DECIMAL
DOUBLE_NEGATIVE	      :	    "-" DOUBLE
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

sparql_lark = Lark(grammar, start="queryunit", parser="lalr", maybe_placeholders=False)

class Print_Tree(Visitor):
    def print_quotation(self, tree):
        assert tree.data == "quotation"
        print(tree.children)

from lark import Visitor, v_args

tree = sparql_lark.parse(sparqlbytes_processing)
quotation_dict = []
quotationreif = []

def myHash(text:str):
  return str(hashlib.md5(text.encode('utf-8')).hexdigest())

print(tree)
class FindVariables(Visitor):
    def __init__(self):
        super().__init__()
        # self.quotation_list = []
        self.variable_list = []

    def quotation(self, var):

        qut = Reconstructor(sparql_lark).reconstruct(var) # replace here or replace later
        print("qqqqqqqqqqqqqqqqqqqqqqqqqqq", qut,"\n" )
        qut = qut.replace(";", "") #####################
        # qut = qut.replace(" ", "") #qut = qut.strip()
        if not (qut in sparql_lark):
            sparql_lark.append(qut)

        vr = Reconstructor(sparql_lark).reconstruct(var)
        vr = vr.replace(";","")
        # vr = vr.replace(" ","")
        sparql_lark[qut] = str(myHash(qut))
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
                oa1 = Reconstructor(sparql_lark).reconstruct(var)
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

    # def blank_node_property_list(self, var):
    #     # print("bnpl", (var.children[0]).children)
    #     object_list = ((var.children[0]).children)[1].children
    #     for x in range(0, len(object_list)):
    #         try:
    #             if object_list[x].data == 'quotation':
    #                 # print("fixing blank node property list:", object_list, "\n","\n")
    #                 collection_quotation_reconstruct = Reconstructor(turtle_lark).reconstruct(object_list[x])
    #                 collection_quotation_reconstruct = collection_quotation_reconstruct.replace(";","")
    #                 t2 = quotation_dict[collection_quotation_reconstruct]
    #                 hasht2 = "_:" + t2
    #                 object_list[x] = Tree('iri', [Tree('prefixed_name', [Token('PNAME_LN', hasht2)])])
    #                 # print("iriririri", object_list)
    #         except:
    #             pass
    # def collection(self, var):
    #     for x in range(0, len(var.children)):
    #         if var.children[x].data == 'quotation':
    #             # print("fixing collection:", x, "\n","\n")
    #             collection_quotation_reconstruct = Reconstructor(turtle_lark).reconstruct(var.children[x])
    #             collection_quotation_reconstruct = collection_quotation_reconstruct.replace(";","")
    #             t2 = quotation_dict[collection_quotation_reconstruct]
    #             hasht2 = "_:" + t2
    #             var.children[x] = Tree('iri', [Tree('prefixed_name', [Token('PNAME_LN', hasht2)])])
    #             # print("iriririri", var.children)

    # def quotedtriples(self, var):
    #     triple1 = None
    #     subjecthash = ""

    #     for x in var.children:
    #         print(x)
    #         if x.data == "triples":
    #             triple1 = Reconstructor(turtle_lark).reconstruct(x)
    #             triple1 = triple1.replace(";","")

    #             print(triple1)
    #             triple1 = "<<"+triple1+">>"
    #             subjecthash = "_:" + str(myHash(triple1))
    #             print("teststestt", triple1)
    #             print(subjecthash)

    #         elif x.data == "compoundanno":
    #             for y in x.children:
    #                 if (y != "{|") & (y!= "|}"):
    #                     count2 = 0
    #                     quotationtriple = []
    #                     for z in y.children:
    #                         count2+=1
    #                         z2 = Reconstructor(turtle_lark).reconstruct(z)
    #                         # z2 = z2.replace(";","")
    #                         print("z",z2)
    #                         quotationtriple.append(z2)
    #                         if count2 ==2:
    #                             quotationtriple.insert(0, subjecthash)
    #                             quotationannolist.append(quotationtriple)
    #                             count2 = 0
    #                             quotationtriple = []

    # def triples(self, var):

    #     appends1 = []
    #     tri = Reconstructor(turtle_lark).reconstruct(var)
    #     print("ttttttttttttttttttttttttttttt", tri,"\n" )
    #     tri = tri.replace(";", "")
    #     if not (tri in assertedtriplelist):
    #         assertedtriplelist.append(tri)
    #     for x in var.children:
    #         # print(x.data)
    #         if x.data == 'predicate_object_list':
    #             xc = x.children
    #             for y in xc:
    #                 x2 = Reconstructor(turtle_lark).reconstruct(y)
    #                 x2 = x2.replace(";","")
    #                 # x2 = x2.replace(" ","")
    #                 appends1.append(x2) # or push
    #         else:
    #           print("how to edit2", x)
    #           anyquotationin = False
    #           x1 = Reconstructor(turtle_lark).reconstruct(x)
    #           x1 = x1.replace(";","")
    #         #   x1 = x1.replace(" ","")
    #           print("compareed", x1)
    #           appends1.append(x1)

    #     if not (appends1 in vblist):
    #         vblist.append(appends1)

    # def insidequotation(self, var):
    #     appends1 = []
    #     for x in var.children:
    #         x1 = Reconstructor(turtle_lark).reconstruct(x)
    #         x1 = x1.replace(";","")
    #         # x1 = x1.replace(" ","")
    #         appends1.append(x1)

    #     if not (appends1 in vblist):
    #         vblist.append(appends1)

    # def prefixed_name(self, children):
    #     print("prefixed_name")
    #     # pname, = children
    #     print("pn", children)
    #     # ns, _, ln = pname.partition(':')
    #     # return self.make_named_node(self.prefixes[ns] + decode_literal(ln))

    # def prefix_id(self, children):
    #     print("prefix_id")
    #     ns, iriref = children
    #     print("prefix_id", ns, iriref)
    #     iri = smart_urljoin(self.base_iri, self.decode_iriref(iriref))
    #     print(iri)
    #     ns = ns[:-1]  # Drop trailing : from namespace
    #     # self.prefixes[ns] = iri
    #     # return []

    # def sparql_prefix(self, children):
    #     print("sparql_prefix", children)
    #     prefix_list.append(children)

    # def base(self, children):
    #     print("base")
    #     base_directive, base_iriref = children
    #     print("base", base_directive, base_iriref)
    #     # Workaround for lalr parser token ambiguity in python 2.7
    #     if base_directive.startswith('@') and base_directive != '@base':
    #         raise ValueError('Unexpected @base: ' + base_directive)

# at = FindVariables().visit(tree)
# res = g.query("SELECT * { <<:a :b :c>> ?p ?o }")
# print(list(res))
