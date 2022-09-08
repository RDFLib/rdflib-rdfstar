from rdflib import ConjunctiveGraph
from rdflib.parser import Parser
from .notation3 import SinkParser, RDFSink

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

grammar = r"""trig_doc: (directive | block)*
?statement: directive | triples "." | quotedtriples "."
block: triplesorgraph | wrappedgraph | triples2 | "GRAPH" labelorsubject wrappedgraph
triplesorgraph: labelorsubject (wrappedgraph | predicate_object_list ".") | quotation predicate_object_list "."
triples2: blank_node_property_list predicate_object_list? "." | collection predicate_object_list "."
wrappedgraph: "{" triplesblock? "}"
triplesblock: triples ("." triplesblock?)? | quotedtriples ("." triplesblock?)?
labelorsubject: iri | blank_node
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
?object_list: object ("," object )*
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

trig_lark = Lark(grammar, start="trig_doc", parser="lalr", maybe_placeholders = False)

class Print_Tree(Visitor):
    def print_quotation(self, tree):
        assert tree.data == "quotation"
        print(tree.children)

from lark import Visitor, v_args
quotation_list = []
quotation_dict = dict()
vblist = []
quotationreif = []
prefix_list = []
quotationannolist = []
constructors = ""
assertedtriplelist = []
quoted_or_not = False
both_quoted_and_asserted = False

def myHash(text:str):
  return str(hashlib.md5(text.encode('utf-8')).hexdigest())

class FindVariables(Visitor):
    def __init__(self):
        super().__init__()
        # self.quotation_list = []
        self.variable_list = []

    def quotation(self, var):
        qut = Reconstructor(trig_lark).reconstruct(var) # replace here or replace later
        qut = qut.replace(";", "") #####################
        # qut = qut.replace(" ", "") #qut = qut.strip()
        # print("qqqqqqqqq", qut)
        if not (qut in quotation_list):
            quotation_list.append(qut)

        vr = Reconstructor(trig_lark).reconstruct(var)
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
                oa1 = Reconstructor(trig_lark).reconstruct(var)
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

    def blank_node_property_list(self, var):
        # print("bnpl", (var.children[0]).children)
        object_list = ((var.children[0]).children)[1].children
        for x in range(0, len(object_list)):
            try:
                if object_list[x].data == 'quotation':
                    print("normal", object_list)
                    # print("fixing blank node property list:", object_list, "\n","\n")
                    collection_quotation_reconstruct = Reconstructor(trig_lark).reconstruct(object_list[x])
                    collection_quotation_reconstruct = collection_quotation_reconstruct.replace(";","")
                    t2 = quotation_dict[collection_quotation_reconstruct]
                    hasht2 = "_:" + t2
                    object_list[x] = Tree('iri', [Tree('prefixed_name', [Token('PNAME_LN', hasht2)])])
                    # print("iriririri", object_list)
            except Exception as ex:
                # print(ex, "blank node property list is not nested")
                object_list = ((var.children[0]).children)[1]
                collection_quotation_reconstruct = Reconstructor(trig_lark).reconstruct(object_list)
                collection_quotation_reconstruct = collection_quotation_reconstruct.replace(";","")
                try:
                    t2 = quotation_dict[collection_quotation_reconstruct]
                    hasht2 = "_:" + t2
                    ((var.children[0]).children)[1] = Tree('iri', [Tree('prefixed_name', [Token('PNAME_LN', hasht2)])])
                    break
                except Exception as ex2:
                    pass

    def collection(self, var):
        for x in range(0, len(var.children)):
            if var.children[x].data == 'quotation':
                # print("fixing collection:", x, "\n","\n")
                collection_quotation_reconstruct = Reconstructor(trig_lark).reconstruct(var.children[x])
                collection_quotation_reconstruct = collection_quotation_reconstruct.replace(";","")
                t2 = quotation_dict[collection_quotation_reconstruct]
                hasht2 = "_:" + t2
                var.children[x] = Tree('iri', [Tree('prefixed_name', [Token('PNAME_LN', hasht2)])])

    def quotedtriples(self, var):
        triple1 = None
        subjecthash = ""

        for x in var.children:
            print(x)
            if x.data == "triples":
                triple1 = Reconstructor(trig_lark).reconstruct(x)
                triple1 = triple1.replace(";","")

                print(triple1)
                triple1 = "<<"+triple1+">>"
                subjecthash = "_:" + str(myHash(triple1))
                print(subjecthash)
                if not (triple1 in quotation_list):
                    quotation_list.append(triple1)

                quotation_dict[triple1] = str(myHash(triple1))
            elif x.data == "compoundanno":
                for y in x.children:
                    if (y != "{|") & (y!= "|}"):
                        count2 = 0
                        quotationtriple = []
                        for z in y.children:
                            count2+=1
                            z2 = Reconstructor(trig_lark).reconstruct(z)
                            # z2 = z2.replace(";","")
                            print("z",z2)
                            quotationtriple.append(z2)
                            if count2 ==2:
                                quotationtriple.insert(0, subjecthash)
                                quotationannolist.append(quotationtriple)
                                count2 = 0
                                quotationtriple = []

    def triples(self, var):

        appends1 = []
        tri = Reconstructor(trig_lark).reconstruct(var)
        # print("ttttttttttttttttttttttttttttt", tri,"\n" )
        tri = tri.replace(";", "")
        if not (tri in assertedtriplelist):
            assertedtriplelist.append(tri)
        for x in var.children:
            if x.data == 'predicate_object_list':
                xc = x.children
                for y in xc:
                    x2 = Reconstructor(trig_lark).reconstruct(y)
                    x2 = x2.replace(";","")
                    # x2 = x2.replace(" ","")
                    appends1.append(x2) # or push
            else:
            #   print("how to edit2", x)
              anyquotationin = False
              x1 = Reconstructor(trig_lark).reconstruct(x)
              x1 = x1.replace(";","")
            #   x1 = x1.replace(" ","")
            #   print("compareed", x1)
              appends1.append(x1)

        if not (appends1 in vblist):
            vblist.append(appends1)

    def insidequotation(self, var):
        appends1 = []
        for x in var.children:
            x1 = Reconstructor(trig_lark).reconstruct(x)
            x1 = x1.replace(";","")
            # x1 = x1.replace(" ","")
            appends1.append(x1)

        if not (appends1 in vblist):
            vblist.append(appends1)

    # def prefixed_name(self, children):
    #     print("prefixed_name")
    #     print("pn", self)

    def prefix_id(self, children):
        print("prefix_id")

    def sparql_prefix(self, children):
        print("sparql_prefix", children)
        prefix_list.append(children)

    def base(self, children):
        print("base")
        base_directive, base_iriref = children
        print("base", base_directive, base_iriref)
        # Workaround for lalr parser token ambiguity in python 2.7
        if base_directive.startswith('@') and base_directive != '@base':
            raise ValueError('Unexpected @base: ' + base_directive)

def RDFstarParsings(rdfstarstring):
    global quotationannolist, quotation_dict, vblist, quotationreif, prefix_list, constructors, assertedtriplelist, quoted_or_not, both_quoted_and_asserted
    quotationannolist = []
    vblist = []
    quotationreif = []
    prefix_list = []
    constructors = ""
    quoted_or_not = False
    both_quoted_and_asserted = False
    tree = trig_lark.parse(rdfstarstring)
    at = FindVariables().visit(tree)

    for y in vblist:
        # print("warc3casca", y)
        for element_index in range(0, len(y)):
            if (y[element_index][0] == "_") & (not (element_index == 0)):
                y[element_index]=" "+y[element_index]
        result = "".join(y)
        result = result.replace(" ", "")
        if result in assertedtriplelist:
            test1 = "<<"+result+">>"
            if test1 in quotation_list:
                both_quoted_and_asserted = True
            else:
                both_quoted_and_asserted = False
                quoted_or_not = False
        else:
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
        if result1 in quotation_list:
            both_quoted_and_asserted = True
        else:
            both_quoted_and_asserted = False
            quoted_or_not = False
        value = str(myHash(result1))
        subject = z[0]
        predicate = z[1]
        object = z[2]
        if both_quoted_and_asserted:
            next_rdf_object = "_:" + str(value) + '\n' + "    a rdfstar:AssertedStatement, rdfstar:QuotedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
        else:
            if quoted_or_not:
                next_rdf_object = "_:" + str(value) + '\n' + "    a rdfstar:QuotedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
            else:
                next_rdf_object = "_:" + str(value) + '\n' + "    a rdfstar:AssertedStatement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n"
        constructors+=next_rdf_object

    for x in range(0, len(prefix_list)):
        prefix_list[x] = Reconstructor(trig_lark).reconstruct(prefix_list[x])
        constructors = prefix_list[x]+"\n"+constructors

    constructors = "PREFIX rdfstar: <https://w3id.org/rdf-star/> \n"+constructors

    constructors = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \n"+constructors

    # constructors = "PREFIX : <http://example/> \n"+constructors # prefix

    if not (("PREFIX : <http://example/>" in constructors) or ("PREFIX:<http://example/>" in constructors)):
        constructors = "PREFIX : <http://example/> \n"+constructors

    if "PREFIX:" in constructors:
        constructors = constructors.replace("PREFIX:", "PREFIX :")

    print("yes?", constructors)
    constructors = bytes(constructors, 'utf-8')
    return constructors

def becauseSubGraph(*args, **kwargs):
    pass


class TrigSinkParser(SinkParser):
    def directiveOrStatement(self, argstr, h):

        # import pdb; pdb.set_trace()

        i = self.skipSpace(argstr, h)
        if i < 0:
            return i  # EOF

        j = self.graph(argstr, i)
        if j >= 0:
            return j

        j = self.sparqlDirective(argstr, i)
        if j >= 0:
            return j

        j = self.directive(argstr, i)
        if j >= 0:
            return self.checkDot(argstr, j)

        j = self.statement(argstr, i)
        if j >= 0:
            return self.checkDot(argstr, j)

        return j

    def labelOrSubject(self, argstr, i, res):
        j = self.skipSpace(argstr, i)
        if j < 0:
            return j  # eof
        i = j

        j = self.uri_ref2(argstr, i, res)
        if j >= 0:
            return j

        if argstr[i] == "[":
            j = self.skipSpace(argstr, i + 1)
            if j < 0:
                self.BadSyntax(argstr, i, "Expected ] got EOF")
            if argstr[j] == "]":
                res.append(self.blankNode())
                return j + 1
        return -1

    def graph(self, argstr, i):
        """
        Parse trig graph, i.e.

           <urn:graphname> = { .. triples .. }

        return -1 if it doesn't look like a graph-decl
        raise Exception if it looks like a graph, but isn't.
        """

        # import pdb; pdb.set_trace()
        j = self.sparqlTok("GRAPH", argstr, i)  # optional GRAPH keyword
        if j >= 0:
            i = j

        r = []
        j = self.labelOrSubject(argstr, i, r)
        if j >= 0:
            graph = r[0]
            i = j
        else:
            graph = self._store.graph.identifier  # hack

        j = self.skipSpace(argstr, i)
        if j < 0:
            self.BadSyntax(argstr, i, "EOF found when expected graph")

        if argstr[j : j + 1] == "=":  # optional = for legacy support

            i = self.skipSpace(argstr, j + 1)
            if i < 0:
                self.BadSyntax(argstr, i, "EOF found when expecting '{'")
        else:
            i = j

        if argstr[i : i + 1] != "{":
            return -1  # the node wasn't part of a graph

        j = i + 1

        oldParentContext = self._parentContext
        self._parentContext = self._context
        reason2 = self._reason2
        self._reason2 = becauseSubGraph
        self._context = self._store.newGraph(graph)

        while 1:
            i = self.skipSpace(argstr, j)
            if i < 0:
                self.BadSyntax(argstr, i, "needed '}', found end.")

            if argstr[i : i + 1] == "}":
                j = i + 1
                break

            j = self.directiveOrStatement(argstr, i)
            if j < 0:
                self.BadSyntax(argstr, i, "expected statement or '}'")

        self._context = self._parentContext
        self._reason2 = reason2
        self._parentContext = oldParentContext
        # res.append(subj.close())    # No use until closed
        return j


class TrigParser(Parser):
    """
    An RDFLib parser for TriG

    """

    def __init__(self):
        pass

    def parse(self, source, graph, encoding="utf-8"):

        if encoding not in [None, "utf-8"]:
            raise Exception(
                ("TriG files are always utf-8 encoded, ", "I was passed: %s") % encoding
            )

        # we're currently being handed a Graph, not a ConjunctiveGraph
        assert graph.store.context_aware, "TriG Parser needs a context-aware store!"

        conj_graph = ConjunctiveGraph(store=graph.store, identifier=graph.identifier)
        conj_graph.default_context = graph  # TODO: CG __init__ should have a
        # default_context arg
        # TODO: update N3Processor so that it can use conj_graph as the sink
        conj_graph.namespace_manager = graph.namespace_manager

        sink = RDFSink(conj_graph)

        baseURI = conj_graph.absolutize(
            source.getPublicId() or source.getSystemId() or ""
        )
        p = TrigSinkParser(sink, baseURI=baseURI, turtle=True)

        # stream = source.getCharacterStream()  # try to get str stream first
        # if not stream:
        #     # fallback to get the bytes stream
        #     stream = source.getByteStream()
        if hasattr(source, "file"):
            f = open(source.file.name, "rb")
            rdbytes = f.read()
            f.close()
        elif hasattr(source, "_InputSource__bytefile"):
            if hasattr(source._InputSource__bytefile, "wrapped"):
                f = open((source._InputSource__bytefile.wrapped.strip().splitlines())[0], "rb") # what if multiple files
                rdbytes = f.read()
                f.close()
        bp = rdbytes.decode("utf-8")
        ou = RDFstarParsings(bp)

        # p.loadStream(ou)
        # print("sadadasdasdad",ou)
        p.feed(ou)
        p.endDoc()
        for prefix, namespace in p._bindings.items():
            conj_graph.bind(prefix, namespace)

        # return ???
