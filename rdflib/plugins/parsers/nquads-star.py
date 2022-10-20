import collections
import hashlib
import logging
import re
from threading import local

import rdflib

__all__ = [
    "BaseParser",
    "decode_literal",
    "grouper",
    "smart_urljoin",
    "validate_iri",
]

log = logging.getLogger(__name__)


ESCAPE_MAP = {
    "t": "\t",
    "b": "\b",
    "n": "\n",
    "r": "\r",
    "f": "\f",
    '"': '"',
    "'": "'",
    "\\": "\\",
}


def process_escape(escape):

    escape = escape.group(0)[1:]

    if escape[0] in ("u", "U"):
        return chr(int(escape[1:], 16))
    else:
        return ESCAPE_MAP.get(escape[0], escape[0])


def decode_literal(literal):
    return re.sub(
        r"\\u[a-fA-F0-9]{4}|\\U[a-fA-F0-9]{8}|\\[^uU]", process_escape, literal
    )


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"

    from itertools import zip_longest

    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def smart_urljoin(base, url):
    """urljoin, only an empty fragment from the relative(?) URL will be
    preserved.
    """
    from urllib.parse import urljoin

    joined = urljoin(base, url)
    if url.endswith("#") and not joined.endswith("#"):
        joined += "#"
    return joined


LEGAL_IRI = re.compile(r'^[^\x00-\x20<>"{}|^`\\]*$')


def validate_iri(iri):
    if not LEGAL_IRI.match(iri):
        raise ValueError(f"Illegal characters in IRI: “{iri}”")
    return iri


class BaseParser:
    """Common base class for all parsers
    Provides shared utilities for creating RDF objects, handling IRIs, and
    tracking parser state.
    """

    def __init__(self, sink=None):
        self.sink = sink if sink is not None else rdflib.graph.Dataset()
        # self.profile = Profile()
        self.profile = {}
        self._call_state = local()

    def make_blank_node(self, label=None):
        if label:
            if label in self._call_state.bnodes:
                node = self._call_state.bnodes[label]
            else:
                if self.preserve_bnode_ids is True:
                    node = rdflib.BNode(label[2:])
                else:
                    if self.bidprefix is None:
                        node = rdflib.BNode()
                    else:
                        node = rdflib.BNode(
                            f"{self.bidprefix}{self._call_state.bidcounter:0}"
                        )
                        self._call_state.bidcounter += 1
                self._call_state.bnodes[label] = node
        else:
            if self.bidprefix is None:
                node = rdflib.BNode()
            else:
                node = rdflib.BNode(f"{self.bidprefix}{self._call_state.bidcounter:0}")
                self._call_state.bidcounter += 1
            self._call_state.bnodes[node.n3()] = node
        return node

    def make_quotedgraph(self, store=None):
        self._call_state.formulacounter += 1
        return rdflib.graph.QuotedGraph(
            store=self._call_state.graph.store if store is None else store,
            identifier=f"Formula{self._call_state.formulacounter}",
        )

    def make_rdfstartriple(self, subject, predicate, object):
        rdflib.logger.info(f"make_rdfstartriple: ({subject}, {predicate}, {object})")
        sid = str(
            hashlib.md5((subject + predicate + object).encode("utf-8")).hexdigest()
        )
        return rdflib.experimental.term.RDFStarTriple(sid, subject, predicate, object)

    def _prepare_parse(self, graph):
        self._call_state.bnodes = collections.defaultdict(rdflib.term.BNode)
        self._call_state.graph = graph
        self._call_state.bidcounter = 1
        self._call_state.formulacounter = 0

    def _cleanup_parse(self):
        del self._call_state.bnodes
        del self._call_state.graph
        del self._call_state.bidcounter
        del self._call_state.formulacounter

    def _make_graph(self):
        return rdflib.ConjunctiveGraph()

"""Parse RDF serialized as nquads files.
Usage::
If ``.parse()`` is called with a file-like object implementing ``readline``,
it will efficiently parse line by line rather than parsing the entire file.
"""
import hashlib
import os
from urllib.parse import urlparse

import lark_cython
from lark import Lark, Transformer

import rdflib

from rdflib.term import RdfstarTriple


class NQuadsStarTransformer(BaseParser, Transformer):
    """Transform the tokenized ntriples into RDF primitives."""

    def __init__(self, base_iri=""):
        super().__init__()
        self.base_iri = base_iri
        self.prefixes = self.profile
        self.preserve_bnode_ids = True
        self.bidprefix = None
        self.context = None
        self.annotations = {}

    def blank_node_label(self, children):
        (bn_label,) = children
        return self.make_blank_node(bn_label.value)

    def decode_iriref(self, iriref):
        assert urlparse(iriref.value[1:-1]).scheme != ""
        return validate_iri(decode_literal(iriref.value[1:-1]))

    def iriref(self, children):
        (iriref_or_pname,) = children

        if iriref_or_pname.value.startswith("<"):
            assert " " not in iriref_or_pname.value, iriref_or_pname
            return rdflib.URIRef(self.decode_iriref(iriref_or_pname))

        return iriref_or_pname

    def literal(self, children):
        quoted_literal = children[0]

        quoted_literal = quoted_literal.value[1:-1]  # Remove ""s
        literal = decode_literal(quoted_literal)

        if len(children) == 2 and children[1].type == "IRIREF":
            datatype = children[1]
            return rdflib.Literal(literal, datatype=self.decode_iriref(datatype))

        elif len(children) == 2 and children[1].type == "LANGTAG":
            lang = children[1].value[1:]  # Remove @
            return rdflib.Literal(literal, lang=lang)
        else:
            return rdflib.Literal(literal, lang=None)

    def subject_or_object(self, children):
        # child[0] is a Triple if the subject is a quoted statement
        if isinstance(children[0], tuple):
            q = self.quotedstatement(children)
            self._call_state.graph.add(q)

        else:
            # Just an non-embedded term
            return children[0]

    def subject(self, children):
        return self.subject_or_object(children)

    def object(self, children):
        return self.subject_or_object(children)

    def quotedstatement(self, children):
        s, p, o = children
        hashid = hashlib.md5("-".join(children).encode("utf-8")).hexdigest()
        try:
            q = self.annotations[hashid]
        except KeyError:
            q = RdfstarTriple(hashid)
            q.setsubject(s)
            q.setpredicate(p)
            q.setobject(o)
            self.annotations[hashid] = q
        return q

    def statement(self, children):
        if len(children) == 3:
            subject, predicate, object_ = children
            graph = rdflib.graph.DATASET_DEFAULT_GRAPH_ID
        else:
            subject, predicate, object_, graph = children

        self.context = graph
        self._call_state.graph.addN([(subject, predicate, object_, graph)])
        return children

    def start(self, children):
        for child in children:
            yield child


nqstar_lark = Lark(
    open(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "grammar", "nquads-star.lark")
        ),
        "r",
    ).read(),
    parser="lalr",
    transformer=NQuadsStarTransformer(),
    _plugins=lark_cython.plugins,
)


class LarkNQuadsStarParser(rdflib.parser.Parser):
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

        # W3C test suite authors create tests for whitespace and
        # comment processing, unfortunately omitted from the
        # NTriples EBNF grammar specification.

        uncommented_input = "\n".join(
            [s.strip() for s in string.split("\n") if not s.startswith("#") and s != ""]
        )

        tf = nqstar_lark.options.transformer
        tf.preserve_bnode_ids = kwargs.get("preserve_bnode_ids", False)
        tf.bidprefix = kwargs.get("bidprefix", None)
        bindings = kwargs.get("bindings", dict())

        if graph is None:
            graph = tf._make_graph()

        for p, n in rdflib.namespace._NAMESPACE_PREFIXES_CORE.items():
            if p not in tf.prefixes:
                tf.prefixes[p] = n

        for p, n in bindings.items():
            if p not in tf.prefixes:
                tf.prefixes[p] = n

        for p, n in tf.prefixes.items():
            graph.bind(p, n)

        tf._prepare_parse(graph)

        statements = nqstar_lark.parse(uncommented_input)

        tf._cleanup_parse()

        return graph

    def parse_string(self, string_or_bytes, graph=None, base=""):
        return self.parse(string_or_bytes, graph, base)
