# -*- coding: utf-8 -*-
"""Parse RDF serialized as turtle files.

Unlike the ntriples parser, this parser cannot efficiently parse turtle line
by line. If a file-like object is provided, the entire file will be read into
memory and parsed there.

"""
import hashlib
import os

import lark_cython
from lark import Lark, Transformer, Tree
import rdflib
from rdflib.experimental.plugins.parsers.parserutil import (
    BaseParser,
    decode_literal,
    grouper,
    smart_urljoin,
    validate_iri,
)
from rdflib.term import RdfstarTriple

RDF_TYPE = rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
RDF_NIL = rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#nil")
RDF_FIRST = rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#first")
RDF_REST = rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest")

XSD_DECIMAL = rdflib.URIRef("http://www.w3.org/2001/XMLSchema#decimal")
XSD_DOUBLE = rdflib.URIRef("http://www.w3.org/2001/XMLSchema#double")
XSD_INTEGER = rdflib.URIRef("http://www.w3.org/2001/XMLSchema#integer")
XSD_BOOLEAN = rdflib.URIRef("http://www.w3.org/2001/XMLSchema#boolean")
XSD_STRING = rdflib.URIRef("http://www.w3.org/2001/XMLSchema#string")

RDFLIB_OBJECTS = (
    rdflib.BNode,
    rdflib.Literal,
    rdflib.URIRef,
    RdfstarTriple,
)

annotatables = []


def unpack_predicateobjectlist(subject, pol):
    global annotatables
    if not isinstance(subject, RDFLIB_OBJECTS):
        for triple_or_node in subject:
            if isinstance(triple_or_node, tuple):
                yield triple_or_node
            else:
                subject = triple_or_node
                break

    for predicate, object_ in grouper(pol, 2):

        if isinstance(predicate, lark_cython.lark_cython.Token):
            if predicate != "a":
                raise ValueError(predicate)
            predicate = RDF_TYPE

        if isinstance(object_, RDFLIB_OBJECTS):
            yield (subject, predicate, object_)

        else:

            if isinstance(object_, Tree):
                object_ = object_.children

            for object_item in object_:

                if isinstance(object_item, tuple):
                    annotatables.append(object_item)
                    yield object_item

                elif isinstance(object_item, list):

                    if annotatables != []:
                        yield [annotatables[0], object_item]
                        annotatables = []
                    else:
                        raise Exception("W-I-P")
                else:
                    annotatables.append([subject, predicate, object_item])
                    yield (subject, predicate, object_item)


class TurtleStarTransformer(BaseParser, Transformer):
    def __init__(self, base_iri=""):
        super().__init__()
        self.base_iri = base_iri
        self.prefixes = self.profile
        self.preserve_bnode_ids = True
        self.rdfstar_triples = {}
        self.bidprefix = None

    def decode_iriref(self, iriref):
        iriref = (
            iriref.value
            if isinstance(iriref, lark_cython.lark_cython.Token)
            else iriref
        )
        return validate_iri(decode_literal(iriref[1:-1]))

    def iri(self, children):
        (iriref_or_pname,) = children
        iriref_or_pname = (
            iriref_or_pname
            if isinstance(iriref_or_pname, rdflib.URIRef)
            else iriref_or_pname.value
        )
        if iriref_or_pname.startswith("<"):
            return rdflib.URIRef(
                smart_urljoin(self.base_iri, self.decode_iriref(iriref_or_pname))
            )

        return iriref_or_pname

    def predicateobjectlist(self, children):
        return children

    def objectlist(self, children):
        return children

    def quotedtriple(self, children):
        hashid = hashlib.md5("-".join(children).encode("utf-8")).hexdigest()
        try:
            q = self.rdfstar_triples[hashid]
        except KeyError:
            q = RdfstarTriple(hashid)
            q.setSubject(children[0])
            q.setPredicate(children[1])
            q.setObject(children[2])
            self.rdfstar_triples[hashid] = q
        return q

    def quotesubject(self, children):
        return children[0]

    def quoteobject(self, children):
        if len(children) == 1 and not isinstance(
            children[0], (rdflib.term.Literal, rdflib.term.Node)
        ):
            return self.rdfliteral(children[0])
        else:
            return children[0]

    def annotation(self, children):
        global annotatables
        annotatables += children
        for child in children:
            return child

    def triples(self, children):
        # rdflib.logger.info(f"{children}")
        if len(children) == 1:
            for triple_or_node in children[0]:
                if isinstance(triple_or_node, tuple):
                    self._call_state.graph.add(triple_or_node)
                    yield triple_or_node

        elif len(children) == 2:
            if isinstance(children[0], RdfstarTriple):
                for triple in unpack_predicateobjectlist(children[0], children[1]):
                    self._call_state.graph.add(triple)

            else:
                subject = children[0]
                assertions = []

                for item in unpack_predicateobjectlist(subject, children[1]):

                    if isinstance(item, tuple):
                        self._call_state.graph.add(item)
                        assertions.append(item)
                        yield item

                    elif isinstance(item, list):  # Annotation
                        assertion = assertions.pop()
                        hashid = hashlib.md5(
                            "-".join(assertion).encode("utf-8")
                        ).hexdigest()
                        q = self.rdfstar_triples.get(hashid)
                        if q is None:
                            q = RdfstarTriple(hashid)
                            q.setSubject(assertion[0])
                            q.setPredicate(assertion[1])
                            q.setObject(assertion[2])
                            self.rdfstar_triples[hashid] = q

                        for triple in unpack_predicateobjectlist(q, item[1]):
                            self._call_state.graph.add(triple)
                            yield triple

    def prefixedname(self, children):
        (pname,) = children
        ns, _, ln = pname.value.partition(":")
        return rdflib.URIRef(self.prefixes[ns] + decode_literal(ln))

    def prefixid(self, children):
        ns, iriref = children
        iri = smart_urljoin(self.base_iri, self.decode_iriref(iriref))
        ns = ns.value[:-1]  # Drop trailing : from namespace
        self.prefixes[ns] = iri

        return []

    def sparqlprefix(self, children):
        return self.prefixid(children[1:])

    def base(self, children):
        base_directive, base_iriref = children

        self.base_iri = smart_urljoin(
            self.base_iri, self.decode_iriref(base_iriref.value)
        )

        return []

    def sparqlbase(self, children):
        return self.base(children)

    def blanknode(self, children):
        (bn,) = children

        if bn.type == "ANON":
            return self.make_blank_node()
        elif bn.type == "BLANK_NODE_LABEL":
            return self.make_blank_node(bn.value)
        else:
            raise NotImplementedError()

    def blanknodepropertylist(self, children):
        pl_root = self.make_blank_node()
        for pl_item in unpack_predicateobjectlist(pl_root, children[0]):
            yield pl_item
        yield pl_root

    def collection(self, children):
        prev_node = RDF_NIL
        for value in reversed(children):
            this_bn = self.make_blank_node()
            if not isinstance(value, (rdflib.URIRef, rdflib.Literal, rdflib.BNode)):
                for triple_or_node in value:
                    if isinstance(triple_or_node, tuple):
                        yield triple_or_node
                    else:
                        value = triple_or_node
                        break
            if not isinstance(value, (rdflib.URIRef, rdflib.Literal, rdflib.BNode)):
                yield (
                    this_bn,
                    RDF_FIRST,
                    this_bn,
                )
            else:
                yield (
                    this_bn,
                    RDF_FIRST,
                    value,
                )
            yield (
                this_bn,
                RDF_REST,
                prev_node,
            )
            prev_node = this_bn

        yield prev_node

    def numericliteral(self, children):
        (numeric,) = children

        if numeric.type == "DECIMAL":
            return rdflib.Literal(numeric, datatype=XSD_DECIMAL)
        elif numeric.type == "DOUBLE":
            return rdflib.Literal(numeric, datatype=XSD_DOUBLE)
        elif numeric.type == "INTEGER":
            return rdflib.Literal(numeric, datatype=XSD_INTEGER)
        else:
            raise NotImplementedError(f"{numeric} {type(numeric)} {repr(numeric)}")

    def rdfliteral(self, children):
        literal_string = children[0]
        lang = None
        type_ = None
        if len(children) == 2 and isinstance(children[1], rdflib.URIRef):
            type_ = children[1]
            return rdflib.Literal(literal_string, datatype=type_)
        elif len(children) == 2 and children[1].type == "LANGTAG":
            lang = children[1].value[1:]  # Remove @
            return rdflib.Literal(literal_string, lang=lang)
        else:
            return rdflib.Literal(literal_string, datatype=None)

    def booleanliteral(self, children):
        (boolean,) = children
        return rdflib.Literal(boolean, datatype=XSD_BOOLEAN)

    def astring(self, children):
        (literal,) = children
        if literal.type in (
            "STRING_LITERAL_QUOTE",
            "STRING_LITERAL_SINGLE_QUOTE",
        ):
            string = decode_literal(literal.value[1:-1])
        if literal.type in (
            "STRING_LITERAL_LONG_SINGLE_QUOTE",
            "STRING_LITERAL_LONG_QUOTE",
        ):
            string = decode_literal(literal.value[3:-3])

        return string

    def start(self, children):
        for child in children:
            if not isinstance(child, Tree):
                for triple in child:
                    yield triple


turtlestar_lark = Lark(
    open(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "grammar", "turtle-star.lark")
        ),
        "r",
    ).read(),
    parser="lalr",
    transformer=TurtleStarTransformer(),
    debug=False,
    _plugins=lark_cython.plugins,
)


class LarkTurtleStarParser(rdflib.parser.Parser):
    format = None

    def parse(self, string_or_stream, graph=None, base="", **kwargs):

        if not isinstance(string_or_stream, str) and not isinstance(
            string_or_stream, rdflib.parser.InputSource
        ):
            string_or_stream = rdflib.parser.create_input_source(string_or_stream)
        elif isinstance(string_or_stream, str):
            try:
                validate_iri(string_or_stream)
                string_or_stream = rdflib.parser.create_input_source(string_or_stream)
            except Exception:
                # Is probably data
                pass

        if hasattr(string_or_stream, "readline"):
            string = string_or_stream.read()
        else:
            # Presume string.
            string = string_or_stream

        if isinstance(string_or_stream, bytes):
            string = string_or_stream.decode("utf-8")
        else:
            string = string_or_stream

        # TODO: stringify the remaining input sources
        if isinstance(string, rdflib.parser.FileInputSource):
            string = string.file.read().decode()
        elif isinstance(string, rdflib.parser.StringInputSource):
            string = string.getCharacterStream().read()

        tf = turtlestar_lark.options.transformer
        tf.base_iri = base
        tf.preserve_bnode_ids = kwargs.get("preserve_bnode_ids", False)
        tf.bidprefix = kwargs.get("bidprefix", None)
        bindings = kwargs.get("bindings", dict())

        if graph is None:
            graph = tf._make_graph()

        # for p, n in rdflib.namespace._NAMESPACE_PREFIXES_CORE.items():
        #     if p not in tf.prefixes:
        #         tf.prefixes[p] = n

        for p, n in bindings.items():
            if p not in tf.prefixes:
                tf.prefixes[p] = n

        for p, n in tf.prefixes.items():
            graph.bind(p, n)

        tf._prepare_parse(graph)
        if "{|" in string:
            print("str", string)
            string1 = RDFstarParsings(string)
        else:
            string1 = string
            print("str1", string1)
        statements = list(turtlestar_lark.parse(string1))

        tf._cleanup_parse()

        return graph

    def parse_string(self, string_or_bytes, graph=None, base=""):
        return self.parse(string_or_bytes, graph, base)

import os
import rdflib
from typing import IO, TYPE_CHECKING, Any, Callable, Dict, Optional, TypeVar, Union

from rdflib.term import RdfstarTriple

from rdflib.parser import Parser

if TYPE_CHECKING:
    from rdflib.parser import InputSource

AnyT = TypeVar("AnyT")

nextu=0
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

class Print_Tree(Visitor):
    def print_quotation(self, tree):
        assert tree.data == "quotation"
        print(tree.children)

from lark import Visitor, v_args

annotation_s_p_o = []
annotation_dict = dict()
to_remove = []
output = ""
class Expandanotation(Visitor):
    global annotation_s_p_o, to_remove, annotation_dict
    def __init__(self):
        super().__init__()
        self.variable_list = []

    def triples(self, var):
        tri = Reconstructorv2(turtle_lark).reconstruct(var)
        if "{|" in tri:
            if len(var.children) == 2:
                predicate_object_list2 = var.children[1].children
                subject = Reconstructorv2(turtle_lark).reconstruct(var.children[0])
                po_list = []
                for x in range(0, len(predicate_object_list2)):

                    predicate_or_object = Reconstructorv2(turtle_lark).reconstruct(predicate_object_list2[x])
                    print("all po", predicate_or_object)
                    po_list.append(predicate_or_object)
                    if len(po_list) == 2:
                        if "," in po_list[1]:
                            po_lists = po_list[1].split(",")

                            for y in po_lists:
                                try:
                                    object_annotation = y.split("{|",1)
                                    o1 = object_annotation[0]
                                    a1 = "{|"+object_annotation[1]
                                    a1 = a1.strip()
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
                # if not tri in to_remove:
                #     print("annotation_s_p_o",annotation_s_p_o)
            to_remove.append(tri)
    def compoundanno(self, var):
        appends1 = []
        tri2 = Reconstructorv2(turtle_lark).reconstruct(var)

        for x in var.children[1].children:

            test = Reconstructorv2(turtle_lark).reconstruct(x)
            if "{|" in test:
                test123 = test.split("{|",1)

                object = test123[0]

                test123.pop(0)

                test_annotation = "{|"+ "".join(test123)
                result = annotation_dict[test_annotation]

                appends1.append(object)
                appends1.append(result)
            else:
                appends1.append(test)

        if not tri2 in annotation_dict:
            annotation_dict[tri2] = appends1
        elif not appends1 == annotation_dict[tri2]:
            for x in appends1:
                annotation_dict[tri2].append(x)

def RDFstarParsings(rdfstarstring):
    global to_remove, annotation_s_p_o, output, annotation_dict
    output = ""
    output_tree = ""
    annotation_s_p_o = []
    to_remove = []
    annotation_dict = dict()
    tree = turtle_lark.parse(rdfstarstring)
    tt = Expandanotation().visit(tree)
    tree_after = Reconstructorv2(turtle_lark).reconstruct(tree)
    splittree_after = tree_after.split(">")
    for x in to_remove:
        x = x + " ."
        tree_after = tree_after.replace(x, "")
    tree_after = tree_after+ "\n"
    def expand_to_rdfstar(x):
        global output
        spo = "<<"+x[0] +" "+x[1] + " " + x[2]+">>"
        try:
            if len(x[3]) == 2:
                output += spo + " "+ x[3][0] +" "+x[3][1] + "." + "\n"
            elif len(x[3]) == 3:
                output += spo + " "+ x[3][0] +" "+x[3][1] + "." + "\n"
                newspolist = [spo, x[3][0],x[3][1], x[3][2]]
                expand_to_rdfstar(newspolist)
            else:
                clist = [x[3][y:y+2] for y in range(0, len(x[3]),2)]
                for z in clist:
                    expand_to_rdfstar([x[0],x[1],x[2],z])
        except:
            pass

    output = ""
    for x in annotation_s_p_o:
        output +=x[0] +" "+ x[1] +" "+ x[2] + "." + "\n"
        expand_to_rdfstar(x)

    output_tree = tree_after+output
    # tree = turtle_lark.parse(output_tree)

    # at = FindVariables().visit(tree)

    return output_tree







