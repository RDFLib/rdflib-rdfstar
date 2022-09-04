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

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-basic-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))
# for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
#     print("rwrwrwrwwrww",s)

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-basic-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-bnode-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-bnode-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-bnode-03.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-compound.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-inside-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-inside-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-nested-01.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-syntax-nested-02.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-annotation-1.trig", format = "trigs")
print(g.serialize(format = "trigstar"))

g = Graph()
g.parse(data="test/trig-star/trig-star-annotation-2.trig", format = "trigs")
print(g.serialize(format = "trigstar"))
