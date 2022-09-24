import pytest

from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from rdflib.exceptions import ParserError

from rdflib import Graph, ConjunctiveGraph
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
    "trigs",
    Parser,
    "rdflib.plugins.parsers.trigstar",
    "TrigParser",
)

register(
    "ttlstar",
    Serializer,
    "rdflib.plugins.serializers.turtlestar",
    "TurtlestarSerializer"
)

register(
    "trigstar",
    Serializer,
    "rdflib.plugins.serializers.trigstar",
    "TrigstarSerializer"
)

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-basic-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))
# for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
#     print("rwrwrwrwwrww",s)

g = ConjunctiveGraph()
# print("gscg?t", g.store.context_aware)
# g.parse(data = """PREFIX : <http://example/> \n :G { :s :p :o .   :x :p :d .} """, format = "trig")
g.parse(data = "test/trig-star/trig-star-syntax-basic-02.trig", format = "trigs")
print(g.serialize(format = "trig"))

# for store, (ordered_subjects, subjects, ref) in g._contexts.items():
#     if not ordered_subjects:
#         continue
#     print(store, ordered_subjects, subjects)
    # self._references = ref
    # self._serialized = {}
    # self.store = store
    # self._subjects = subjects

    # if self.default_context and store.identifier == self.default_context:
    #     self.write(self.indent() + "\n{")
    # else:
    #     iri: Optional[str]
    #     if isinstance(store.identifier, BNode):
    #         iri = store.identifier.n3()
    #     else:
    #         iri = self.getQName(store.identifier)
    #         if iri is None:
    #             iri = store.identifier.n3()
    #     self.write(self.indent() + "\n%s {" % iri)

    # self.depth += 1
    # for subject in ordered_subjects:
    #     if self.isDone(subject):
    #         continue
    #     if firstTime:
    #         firstTime = False
    #     if self.statement(subject) and not firstTime:
    #         self.write("\n")
    # self.depth -= 1
    # self.write("}\n")

    # self.endDocument()
    # stream.write("\n".encode("latin-1"))
g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-bnode-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-bnode-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-bnode-03.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-compound.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-inside-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-inside-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-nested-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-syntax-nested-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-annotation-1.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = ConjunctiveGraph()
g.parse(data="test/trig-star/trig-star-annotation-2.trig", format = "trigs")
print(g.serialize(format = "trigstar"))
