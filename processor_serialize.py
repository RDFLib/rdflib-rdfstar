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

g.parse("test/turtle-star/turtle-star-syntax-nested-02.ttl", format = "ttls")
print(g.serialize(format = "ttlstar"))
