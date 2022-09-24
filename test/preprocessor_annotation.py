
import re
# from readline import insert_text
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
from typing import List, Dict, Union, Callable, Iterable, Optional

from lark import Lark
from lark.tree import Tree, ParseTree
from lark.visitors import Transformer_InPlace
from lark.lexer import Token, PatternStr, TerminalDef
from lark.grammar import Terminal, NonTerminal, Symbol

from lark.tree_matcher import TreeMatcher, is_discarded_terminal
from lark.utils import is_id_continue

def is_iter_empty(i):
    try:
        _ = next(i)
        return False
    except StopIteration:
        return True


class WriteTokensTransformer(Transformer_InPlace):
    "Inserts discarded tokens into their correct place, according to the rules of grammar"

    tokens: Dict[str, TerminalDef]
    term_subs: Dict[str, Callable[[Symbol], str]]

    def __init__(self, tokens: Dict[str, TerminalDef], term_subs: Dict[str, Callable[[Symbol], str]]) -> None:
        self.tokens = tokens
        self.term_subs = term_subs

    def __default__(self, data, children, meta):
        if not getattr(meta, 'match_tree', False):
            return Tree(data, children)

        iter_args = iter(children)
        to_write = []
        for sym in meta.orig_expansion:
            if is_discarded_terminal(sym):
                try:
                    v = self.term_subs[sym.name](sym)
                except KeyError:
                    t = self.tokens[sym.name]
                    if not isinstance(t.pattern, PatternStr):
                        raise NotImplementedError("Reconstructing regexps not supported yet: %s" % t)

                    v = t.pattern.value
                to_write.append(v)
            else:
                x = next(iter_args)
                if isinstance(x, list):
                    to_write += x
                else:
                    if isinstance(x, Token):
                        assert Terminal(x.type) == sym, x
                    else:
                        assert NonTerminal(x.data) == sym, (sym, x)
                    to_write.append(x)

        assert is_iter_empty(iter_args)
        return to_write


class Reconstructorv2(TreeMatcher):
    """
    A Reconstructor that will, given a full parse Tree, generate source code.
    Note:
        The reconstructor cannot generate values from regexps. If you need to produce discarded
        regexes, such as newlines, use `term_subs` and provide default values for them.
    Paramters:
        parser: a Lark instance
        term_subs: a dictionary of [Terminal name as str] to [output text as str]
    """

    write_tokens: WriteTokensTransformer

    def __init__(self, parser: Lark, term_subs: Optional[Dict[str, Callable[[Symbol], str]]]=None) -> None:
        TreeMatcher.__init__(self, parser)

        self.write_tokens = WriteTokensTransformer({t.name:t for t in self.tokens}, term_subs or {})

    def _reconstruct(self, tree):
        unreduced_tree = self.match_tree(tree, tree.data)

        res = self.write_tokens.transform(unreduced_tree)
        for item in res:
            if isinstance(item, Tree):
                # TODO use orig_expansion.rulename to support templates
                yield from self._reconstruct(item)
            else:
                yield item

    def reconstruct(self, tree: ParseTree, postproc: Optional[Callable[[Iterable[str]], Iterable[str]]]=None, insert_spaces: bool=True) -> str:
        x = self._reconstruct(tree)
        if postproc:
            x = postproc(x)
        y = []
        prev_item = ''
        for item in x:
            if insert_spaces and prev_item and item and is_id_continue(prev_item[-1]) and is_id_continue(item[0]):
                y.append(' ')
            y.append(item)
            prev_item = item
        return ' '.join(y)

# from pymantic.compat import (
#     binary_type,
# )
# from pymantic.parsers.base import (
#     BaseParser,
# )
# from pymantic.primitives import (
#     BlankNode,
#     Literal,
#     NamedNode,
#     Triple,
# )
# from pymantic.util import (
#     grouper,
#     smart_urljoin,
#     decode_literal,
# )
from pymantic.util import grouper

grammar = r"""turtle_doc: statement*
?statement: directive | triples "."
directive: prefix_id | base | sparql_prefix | sparql_base
prefix_id: "@prefix" PNAME_NS IRIREF "."
base: BASE_DIRECTIVE IRIREF "."
sparql_base: /BASE/i IRIREF
sparql_prefix: /PREFIX/i PNAME_NS IRIREF
triples: subject predicate_object_list
       | blank_node_property_list predicate_object_list?
insidequotation: qtsubject verb qtobject
predicate_object_list: verb object_list (";" (verb object_list)?)*
?object_list: object compoundanno? ("," object compoundanno?)*
?verb: predicate | /a/
?subject: iri | blank_node | collection | quotation
?predicate: iri
?object: iri | blank_node | collection | blank_node_property_list | literal | quotation
?literal: rdf_literal | numeric_literal | boolean_literal
?qtsubject: iri | blank_node | quotation
?qtobject: 	iri | blank_node | literal | quotation
ANGLEBRACKETL: "<<"
ANGLEBRACKETR: ">>"
quotation: ANGLEBRACKETL insidequotation ANGLEBRACKETR
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

turtle_lark = Lark(grammar, start="turtle_doc", parser="lalr", maybe_placeholders=False)

f = open("turtlestar-evaluation/turtle-star-eval-annotation-2.ttl", "rb")
rdbytes = f.read()
f.close()
rdbytes_processing = rdbytes.decode("utf-8")

f1 = open("turtlestar-evaluation/turtle-star-eval-annotation-5.ttl", "rb")
rdbytes1 = f1.read()
f1.close()
rdbytes_processing1 = rdbytes1.decode("utf-8")

f3 = open("turtlestar-evaluation/turtle-star-eval-annotation-3.nt", "rb")
rdbytes3 = f3.read()
f3.close()
rdbytes_processing3 = rdbytes3.decode("utf-8")

f4 = open("turtlestar-evaluation/turtle-star-eval-annotation-4.nt", "rb")
rdbytes4 = f4.read()
f4.close()
rdbytes_processing4 = rdbytes4.decode("utf-8")

object_annotation_list = []
annotation_s_p_o = []
annotation_dict = dict()
to_remove = []
# def unpack_predicate_object_list(subject, pol):
#     # if not isinstance(subject, (NamedNode, BlankNode)):
#     #     for triple_or_node in subject:
#     #         if isinstance(triple_or_node, Triple):
#     #             yield triple_or_node
#     #         else:
#     #             subject = triple_or_node
#     #             break
#     print(subject, pol)
#     for predicate, object_ in grouper(pol, 2):
#         print(predicate, object_)
#         # if isinstance(predicate, Token):
#         #     if predicate.value != 'a':
#         #         raise ValueError(predicate)
#         #     predicate = RDF_TYPE

#         # if not isinstance(object_, (NamedNode, Literal, BlankNode)):
#         #     if isinstance(object_, Tree):
#         #         object_ = object_.children
#         #     for triple_or_node in object_:
#         #         if isinstance(triple_or_node, Triple):
#         #             yield triple_or_node
#         #         else:
#         #             object_ = triple_or_node
#         #             yield Triple(subject, predicate, object_)
#         # else:
#         #     yield Triple(subject, predicate, object_)

class Expandanotation(Visitor):
    global annotation_s_p_o
    def __init__(self):
        super().__init__()
        # self.quotation_list = []
        self.variable_list = []
        # annotation_s_p_o = []

    def triples(self, var):
        print("\nannotationdict\n", annotation_dict)
        # print("arawrawraw", self, var)
        appends1 = []
        tri = Reconstructorv2(turtle_lark).reconstruct(var, insert_spaces = True)
        if "{|" in tri:
            if len(var.children) == 2:
                # unpack_predicate_object_list(var.children[0],var.children[1])
                print("subject","\n", var.children[0],"\n","\n","\n","predicate_object_list","\n",var.children[1])
                print("\n","predicate", var.children[1].children[0], "\n")
                print("\nobject_list", var.children[1].children[1], "\n", len(var.children[1].children),"\n")
                predicate_object_list2 = var.children[1].children # 1
                subject = Reconstructorv2(turtle_lark).reconstruct(var.children[0], insert_spaces = True)
                po_list = []
                # annotation_s_p_o = []
                for x in range(0, len(predicate_object_list2)):
                    # print("firstelement", x.children[0])
                    # print("object", x,"\n")
                    print("object","\n", "\n", len(predicate_object_list2[x].children))
                    print( Reconstructorv2(turtle_lark).reconstruct(predicate_object_list2[x], insert_spaces=True))

                    predicate_or_object = Reconstructorv2(turtle_lark).reconstruct(predicate_object_list2[x], insert_spaces=True)
                    po_list.append(predicate_or_object)
                    print("awdawiudhawiudhawuidhawiu", po_list)
                    if len(po_list) == 2:
                        if "," in po_list[1]:
                            po_lists = po_list[1].split(",") #2121
                            # print("ASdt", po_lists)
                            for y in po_lists:
                                try:
                                    object_annotation = y.split("{|",1)
                                    o1 = object_annotation[0]
                                    a1 = "{|"+object_annotation[1]
                                    a1_Dict = annotation_dict[a1]
                                    spo_list = [subject,po_list[0],o1, a1_Dict]
                                    annotation_s_p_o.append(spo_list)
                                except:
                                    spo_list = [subject,po_list[0],y]
                                    annotation_s_p_o.append(spo_list)
                        else:
                            object_annotation = po_list[1].split("{|",1)
                            o1 = object_annotation[0]
                            a1 = "{|"+object_annotation[1]
                            a1_Dict = annotation_dict[a1]
                            spo_list = [subject, po_list[0], o1, a1_Dict]
                            annotation_s_p_o.append(spo_list)
                        po_list = []
            to_remove.append(tri)
        print("tripleswerawrawrawrawrw", tri,"\n" , annotation_s_p_o)
        for x in var.children:
            x1 = Reconstructorv2(turtle_lark).reconstruct(x, insert_spaces=True)
            print("tripleexpand", x1)
        # print("tripleexpand", var.children[0])
        # if len(tri.split(";"))>2


    def compoundanno(self, var):
        # print("arawrawraw", self, var)
        appends1 = []
        tri2 = Reconstructorv2(turtle_lark).reconstruct(var, insert_spaces=True)
        print("compoundanno", tri2,"\n" )
        # if not tri2 in annotation_dict:

        print(var.children[1])

        for x in var.children[1].children:
            print("sadad", x)
            test = Reconstructorv2(turtle_lark).reconstruct(x, insert_spaces=True)
            print("ersrsrsr", test)
            if "{|" in test:
                test123 = test.split("{|",1)
                print("asdasdsa",test123)
                object = test123[0]
                print("warawrwarawrawr", object)
                # test123 = test123.remove(object) # delete?
                test123.pop(0)
                # print("asdasdsa",test12345)
                test_annotation = "{|"+ "".join(test123)
                result = annotation_dict[test_annotation]
                # print(tri2)
                if not tri2 in annotation_dict:
                    annotation_dict[tri2] = [object,result]
                else:
                    annotation_dict[tri2].append(object)
                    annotation_dict[tri2].append(result)
            else:
                if not tri2 in annotation_dict:
                    annotation_dict[tri2] = [test]
                else:
                    annotation_dict[tri2].append(test)
        # if len(tri.split(";"))>2

    # def predicate_object_list(self, var):
    #     # print("arawrawraw", self, var)
    #     appends1 = []
    #     tri4 = Reconstructorv2(turtle_lark).reconstruct(var)
    #     print("predicate_object_list", tri4,"\n" )
    #     # if "{|" in tri4:
    #     #     object_annotation_list.append(tri35)
    #     # if len(tri.split(";"))>2

    def object_list(self, var):
        # print("arawrawraw", self, var)
        appends1 = []
        tri3 = Reconstructorv2(turtle_lark).reconstruct(var, insert_spaces=True)
        print("object_list", tri3,"\n" )
        if "{|" in tri3:
            object_annotation_list.append(tri3)
        # if len(tri.split(";"))>2

tree = turtle_lark.parse(rdbytes_processing)
print("larkparsertree", tree, "\n")
tt = Expandanotation().visit(tree)
tree_after = Reconstructorv2(turtle_lark).reconstruct(tree, insert_spaces=True)
for x in to_remove:
    x = x + "." #
    print("remove","\n",x)
    tree_after = tree_after.replace(x, "")
    tree_after = tree_after + "\n" #
print("reconstructtree", tree_after)  #
def expand_to_rdfstar(x):
    print("current expand \n\n\n\n",x)
    global output
    # for y in x:
    spo = "<<"+x[0] + " " + x[1] +" "+ x[2]+">>"
    print("ASdsadadasdasd\n\n\n\n\n", spo)
    try: # or lenx <= 3
        if len(x[3]) == 2:
            # print("ASrasrr")
            output += spo + " "+ x[3][0] +" "+x[3][1] + "." + "\n" # smart
            print(output)
        elif len(x[3]) == 3:
            output += spo + " "+ x[3][0] +" "+x[3][1] + "." + "\n" # smart
            newspolist = [spo, x[3][0],x[3][1], x[3][2]]
            expand_to_rdfstar(newspolist)
        else:
            # from stackoverflow
            clist = [x[3][y:y+2] for y in range(0, len(x[3]),2)]
            # print("asdfadsdasdasdd\n\n\n\n\n", clist)
            # print()
            for z in clist:
                # expand_to_rdfstar([x[0],x[1],x[2],z[0],z[1]])
                expand_to_rdfstar([x[0],x[1],x[2],z])
    except:
        # output += x[0] +" "+x[1] + " " + x[2]+ "." + "\n" # smart
        pass


output = ""
for x in annotation_s_p_o:
    # if len(x[3]) ==
    output +=x[0] +" "+ x[1] +" "+ x[2] + "." + "\n"
    expand_to_rdfstar(x)
    print("adding to original", output)
output_tree = tree_after+output

print("output tree", output_tree, '\n', '\n', '\n', '\n', '\n')
annotation_s_p_o = []
annotation_dict = dict()

output = ""

tree1 = turtle_lark.parse(rdbytes_processing1)
print("larkparsertree", tree1, "\n")
tt1 = Expandanotation().visit(tree1)
trrrreeafter = Reconstructorv2(turtle_lark).reconstruct(tt1, insert_spaces=True)
print("reconstructtree", trrrreeafter)
for x in annotation_s_p_o:
    # if len(x[3]) ==
    output +=x[0] +" "+ x[1] +" "+ x[2] + "." + "\n"
    expand_to_rdfstar(x)
    print("adding to original", output)

tree3 = turtle_lark.parse(rdbytes_processing3)
print("larkparsertree3", tree3, "\n", "\n", "\n")
# tt3 = Expandanotation().visit(tree3)


tree5 = turtle_lark.parse(rdbytes_processing4)
print("larkparsertree4", tree5, "\n", "\n", "\n")
# tt43 = Expandanotation().visit(tree5)
