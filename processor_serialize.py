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
# print(g.serialize(format = "ttlstar"))
# for all Statements

# unreified_g = Graph()
# for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
#     unreified_g.add((
#         g.value(s, RDF.subject),
#         g.value(s, RDF.predicate),
#         g.value(s, RDF.object),
#     ))
# print(unreified_g.serialize())

dictionary = dict()
result = ""
for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
    print(s)
    print(
       ( g.value(s, RDF.subject),
       g.value(s, RDF.predicate),
      g.value(s, RDF.object))
      )

    subject = g.value(s, RDF.subject)
    predicate = g.value(s, RDF.predicate)
    object = g.value(s, RDF.object)

    if isinstance(g.value(s, RDF.subject), rdflib.term.BNode):
        if subject in dictionary:
            subject = dictionary[g.value(s, RDF.subject)]
        # else:
        #     subject = "<"+str(subject)+">"

    if isinstance(g.value(s, RDF.object), rdflib.term.BNode):
        if object in dictionary:
            object = dictionary[g.value(s, RDF.object)]
        # else:
        #     object = "<"+str(object)+">"

    # predicate = "<"+str(predicate)+">"



    # print("adada", serialized_subject)

    dictionary[s] = (subject, predicate,object)

    print(type(g.value(s, RDF.object))) # why hash value is changed?

    # print("dictionary", dictionary)

    print("test", subject ,predicate,object)
    # if s == g.value(s, RDF.object):
    #     print("equal")
