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

g.parse("test/turtle-star/turtle-star-syntax-inside-02.ttl", format = "ttls")
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

def expand_Bnode(node, g, dictionary, properties):
    for s, p, o in g.triples((node, None, None)):
        #todo () and []
        # oList = properties.get(p, [])
        # oList.append(o)
        print("atatat", s,p, o)
        print("ptype", type(p))
        if ("http://www.w3.org/1999/02/22-rdf-syntax-ns#first" in p) or ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
            if o in dictionary:
                properties.append(dictionary[o])
            # elif isinstance(o, rdflib.term.BNode):
            #     expand_Bnode(o, g, dictionary,properties)
            # else:
            #     properties.append(o)
            else:
                expand_Bnode(o, g, dictionary,properties)
        else:
            properties.append(p)
            if o in dictionary:
                properties.append(dictionary[o])
            # elif isinstance(o, rdflib.term.BNode):
            #     expand_Bnode(o, g, dictionary,properties)
            # else:
            #     properties.append(o)
            else:
                expand_Bnode(o, g, dictionary,properties)


    return properties

dictionary = dict()
result = ""
for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
    # print(s)
    # print(
    #    ( g.value(s, RDF.subject),
    #    g.value(s, RDF.predicate),
    #   g.value(s, RDF.object))
    #   )

    subject = g.value(s, RDF.subject)
    predicate = g.value(s, RDF.predicate)
    object = g.value(s, RDF.object)

    print("typetest", subject, type(subject), "\n")
    print("current dict", dictionary, "\n")
    properties = []
    # all_changed = True
    # while all_changed:
        # for s, p, o in g.triples((subject, None, None)):
        #     # oList = properties.get(p, [])
        #     # oList.append(o)
        #     if o in dictionary:
        #         properties.append(dictionary(o))
        #     else:
    result = expand_Bnode(subject,g,dictionary,properties)

    print("expand", result, "\n")

    # all_changed = False
    # while (all_changed==False):


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

    # print("before", subject, type(subject))
    if (isinstance(subject, rdflib.term.URIRef)):
        subject = "<"+str(subject)+">"

    if (isinstance(object, rdflib.term.URIRef)):
        object = "<"+str(object)+">"

    if(isinstance(predicate, rdflib.term.URIRef)):
        predicate = "<"+str(g.value(s, RDF.predicate))+">"

    # print("adada", serialized_subject)

    dictionary[s] = "<< "+str(subject)+ str(predicate)+str(object)+" >>"

    # print(type(g.value(s, RDF.object))) # why hash value is changed?

    # print("dictionary", dictionary)

    print("serialize", subject ,predicate,object)
    # if s == g.value(s, RDF.object):
    #     print("equal")

# Todo: how to put this into serializer?

# Todo: how to read in the blanknode to process collection and blank node property list?
# what to discuss with others?
