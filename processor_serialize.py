import pytest

from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from rdflib.exceptions import ParserError

from rdflib import Namespace, Graph
from rdflib.util import guess_format


from rdflib.plugin import register
from rdflib.parser import Parser
from rdflib.serializer import Serializer

import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF
from rdflib.namespace import FOAF

RDFSTAR = Namespace("https://w3id.org/rdf-star/")

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

g.parse("test/turtle-star/nt-ttl-star-bnode-2.ttl", format = "ttls")
# print("testing serializer", g.serialize(format = "ttlstar"))
# for all Statements

# unreified_g = Graph()
# for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
#     unreified_g.add((
#         g.value(s, RDF.subject),
#         g.value(s, RDF.predicate),
#         g.value(s, RDF.object),
#     ))
# print(unreified_g.serialize())

def expand_Bnode(node, g, dictionary, properties, collection_or_not, quoted_Bnode_or_not):
    print("node", node)
    for s, p, o in g.triples((node, None, None)):
        #todo () and []
        # oList = properties.get(p, [])
        # oList.append(o)
        print("atataererererert", dictionary, o, p, "a2a32a3", type(o), type(p))

        if (not "rdf-star" in o):

            # print("ptype", type(p))
            if ("http://www.w3.org/1999/02/22-rdf-syntax-ns#first" in p) or ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
                collection_or_not  =  True
                quoted_Bnode_or_not = False
                if o in dictionary:
                    properties.append(dictionary[o])
                # elif isinstance(o, rdflib.term.BNode):
                #     expand_Bnode(o, g, dictionary,properties)
                # else:
                #     properties.append(o)
                elif not ("http://www.w3.org/1999/02/22-rdf-syntax-ns#nil"  in o):
                    print("recursive", o)

                    if not ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
                        properties.append("(")

                    expand_Bnode(o, g, dictionary,properties, collection_or_not, quoted_Bnode_or_not)

                    if not ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
                        properties.append(")")

            else:
                if (isinstance(o, rdflib.term.URIRef) & isinstance(p, rdflib.term.URIRef)):
                    collection_or_not = False
                    quoted_Bnode_or_not = True
                    print("hererererer")
                    o = "<"+str(o)+">"
                    properties.append(o)
                    if o in dictionary:
                        properties.append(dictionary[o])
                    # elif isinstance(o, rdflib.term.BNode):
                    #     expand_Bnode(o, g, dictionary,properties)
                    # else:
                    #     properties.append(o)
                    else:
                        expand_Bnode(o, g, dictionary,properties, collection_or_not, quoted_Bnode_or_not)
                else:
                    collection_or_not = False
                    quoted_Bnode_or_not = False
                    # print("hererererer")
                    if (isinstance(p, rdflib.term.URIRef)):
                        p = "<"+str(p)+">"
                    else:
                        pass
                    properties.append(p)
                    if o in dictionary:
                        properties.append(dictionary[o])
                    # elif isinstance(o, rdflib.term.BNode):
                    #     expand_Bnode(o, g, dictionary,properties)
                    # else:
                    #     properties.append(o)
                    else:
                        expand_Bnode(o, g, dictionary,properties, collection_or_not, quoted_Bnode_or_not)

    # return properties, collection_or_not, quoted_Bnode_or_not, bnodeid
    return properties, collection_or_not, quoted_Bnode_or_not
    # return properties, collection_or_not, quoted_Bnode_or_not, bnodeid

dictionary = dict()
result_subject = ""
result_object = ""
for s in g.subjects(predicate=RDF.type, object=RDFSTAR.QuotedStatement):
    # print(s)
    # print(
    #    ( g.value(s, RDF.subject),
    #    g.value(s, RDF.predicate),
    #   g.value(s, RDF.object))
    #   )

    subject = g.value(s, RDF.subject)
    predicate = g.value(s, RDF.predicate)
    object = g.value(s, RDF.object)

    print("typetest", subject, type(subject), "\n", predicate, type(predicate), "\n", object, type(subject), "\n")
    # print("current dict", dictionary, "\n")
    properties = []
    collection_or_not = False
    quoted_Bnode_or_not = False
    # all_changed = True
    # while all_changed:
        # for s, p, o in g.triples((subject, None, None)):
        #     # oList = properties.get(p, [])
        #     # oList.append(o)
        #     if o in dictionary:
        #         properties.append(dictionary(o))
        #     else:
    # result, ifcollection = expand_Bnode(subject,g,dictionary,properties,collection_or_not)
    # if ifcollection == True:
    #     result.insert(0, "(")
    #     result.append(")")
    # else:
    #     result.insert(0, "[")
    #     result.append("]")
    # print("expand", result, "\n")

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
        print("tttttttttttuuuuuuuuuuuuuu")
        subject = "<"+str(subject)+">"
    elif (isinstance(subject, rdflib.term.BNode)):
        # print(subject)
        bnode_id = str(subject)
        print("tttttttttttuuuuuuuuuuuuuu22222222222222")
        result_subject, ifcollection, ifquotedBnode = expand_Bnode(subject,g,dictionary,properties,collection_or_not, quoted_Bnode_or_not)
        # print(len(result_subject))
        if (not len(result_subject) == 0):
            if ifcollection == True:
                result_subject.insert(0, "(")
                result_subject.append(")")
            else:
            # if ifquotedBnode == True:
            #     for x in range(0, len(result_subject)):
            #         if isinstance(result_subject[x], rdflib.term.URIRef):
            #             result_subject[x] = "<"+result_subject[x]+">"
            #     # print("ararr", result_subject)
            #     result_subject.insert(0, "<<")
            #     result_subject.append(">>")
            # else:
                result_subject.insert(0, "[")
                result_subject.append("]")
            subject = "".join(result_subject)
        else:
            subject = "[]"
        if subject == "[]":
            subject = " _:"+bnode_id + " "



    if (isinstance(object, rdflib.term.URIRef)):
        object = "<"+str(object)+">"
    elif (isinstance(object, rdflib.term.BNode)):
        print("hererererere")
        # bnode_id2 = str(object)
        bnode_id = str(object)
        result_object, ifcollection, ifquotedBnode = expand_Bnode(subject,g,dictionary,properties,collection_or_not, quoted_Bnode_or_not)
        if (not len(result_object) == 0):
            if ifcollection == True:
                result_object.insert(0, "(")
                result_object.append(")")
            else:
            # if ifquotedBnode == True:
            #     for x in range(0, len(result_subject)):
            #         if isinstance(result_subject[x], rdflib.term.URIRef):
            #             result_subject[x] = "<"+result_subject[x]+">"
            #     # print("ararr", result_subject)
            #     result_subject.insert(0, "<<")
            #     result_subject.append(">>")
            # else:
                result_object.insert(0, "[")
                result_object.append("]")
            object = "".join(result_object)
        else:
            object = "[]"
        if object == "[]":
            object = " _:"+bnode_id + " "

    if(isinstance(predicate, rdflib.term.URIRef)):
        predicate = "<"+str(g.value(s, RDF.predicate))+">"

    # print("adada", serialized_subject)

    dictionary[s] = "<< "+str(subject)+ str(predicate)+str(object)+" >>"

    # print(type(g.value(s, RDF.object))) # why hash value is changed?

    # print("dictionary", dictionary)
    print(properties)
    print("serialize dictionary", subject ,predicate,object)
    # if s == g.value(s, RDF.object):
    #     print("equal")

for s in g.subjects(predicate=RDF.type, object=RDFSTAR.AssertedStatement):
    # print(s)
    # print(
    #    ( g.value(s, RDF.subject),
    #    g.value(s, RDF.predicate),
    #   g.value(s, RDF.object))
    #   )

    subject = g.value(s, RDF.subject)
    predicate = g.value(s, RDF.predicate)
    object = g.value(s, RDF.object)

    print("typetest", subject, type(subject), "\n", predicate, type(predicate), "\n", object, type(object), "\n")
    # print("current dict", dictionary, "\n")
    properties = []
    collection_or_not = False
    quoted_Bnode_or_not = False
    # all_changed = True
    # while all_changed:
        # for s, p, o in g.triples((subject, None, None)):
        #     # oList = properties.get(p, [])
        #     # oList.append(o)
        #     if o in dictionary:
        #         properties.append(dictionary(o))
        #     else:
    # result, ifcollection = expand_Bnode(subject,g,dictionary,properties,collection_or_not)
    # if ifcollection == True:
    #     result.insert(0, "(")
    #     result.append(")")
    # else:
    #     result.insert(0, "[")
    #     result.append("]")
    # print("expand", result, "\n")

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
        print("tttttttttttuuuuuuuuuuuuuu")
        subject = "<"+str(subject)+">"
    elif (isinstance(subject, rdflib.term.BNode)):
        print("tttttttttttuuuuuuuuuuuuuu22222222222222")
        bnode_id = str(subject)
        result_subject, ifcollection, ifquotedBnode = expand_Bnode(subject,g,dictionary,properties,collection_or_not, quoted_Bnode_or_not)
        if ifcollection == True:
            result_subject.insert(0, "(")
            result_subject.append(")")
        else:
            # if ifquotedBnode == True:
            #     for x in range(0, len(result_subject)):
            #         if isinstance(result_subject[x], rdflib.term.URIRef):
            #             result_subject[x] = "<"+result_subject[x]+">"
            #     # print("ararr", result_subject)
            #     result_subject.insert(0, "<<")
            #     result_subject.append(">>")
            # else:
            result_subject.insert(0, "[")
            result_subject.append("]")
        subject = "".join(result_subject)
        if subject == "[]":
            subject = " _:"+bnode_id + " "

    if (isinstance(object, rdflib.term.URIRef)):
        object = "<"+str(object)+">"
    elif (isinstance(object, rdflib.term.BNode)):
        print("hererererere2", str(object))
        bnode_id = str(object)
        result_object, ifcollection, ifquotedBnode = expand_Bnode(object,g,dictionary,properties,collection_or_not, quoted_Bnode_or_not)
        if ifcollection == True:
            result_object.insert(0, "(")
            result_object.append(")")
        else:
            # if ifquotedBnode == True:
            #     for x in range(0, len(result_subject)):
            #         if isinstance(result_subject[x], rdflib.term.URIRef):
            #             result_subject[x] = "<"+result_subject[x]+">"
            #     # print("ararr", result_subject)
            #     result_subject.insert(0, "<<")
            #     result_subject.append(">>")
            # else:
            result_object.insert(0, "[")
            result_object.append("]")
        object = "".join(result_object)
        if object == "[]":
            object = " _:"+bnode_id + " "

    if(isinstance(predicate, rdflib.term.URIRef)):
        predicate = "<"+str(g.value(s, RDF.predicate))+">"

    # print("adada", serialized_subject)

    dictionary[s] = "<< "+str(subject)+ str(predicate)+str(object)+" >>"

    # print(type(g.value(s, RDF.object))) # why hash value is changed?

    # print("dictionary", dictionary)
    print(properties)
    print("serialize", subject ,predicate,object)
    # if s == g.value(s, RDF.object):
    #     print("equal")

# Todo: how to put this into serializer?

# Todo: how to read in the blanknode to process collection and blank node property list?
# what to discuss with others?
