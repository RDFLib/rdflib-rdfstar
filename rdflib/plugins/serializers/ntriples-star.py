"""
HextuplesSerializer RDF graph serializer for RDFLib.
See <https://github.com/ontola/hextuples> for details about the format.
"""
from typing import IO, Optional, Type, Union
import json
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.term import Literal, URIRef, Node, BNode
from rdflib.serializer import Serializer
from rdflib.namespace import RDF, XSD
import warnings
import rdflib

__all__ = ["NtriplesStarSerializer"]


class NtriplesStarSerializer(Serializer):
    """
    Serializes RDF graphs to NTriples format.
    """

    def __init__(self, store: Union[Graph, ConjunctiveGraph]):
        self.default_context: Optional[Node]
        self.graph_type: Type[Graph]
        if isinstance(store, ConjunctiveGraph):
            self.graph_type = ConjunctiveGraph
            self.contexts = list(store.contexts())
            if store.default_context:
                self.default_context = store.default_context
                self.contexts.append(store.default_context)
            else:
                self.default_context = None
        else:
            self.graph_type = Graph
            self.contexts = [store]
            self.default_context = None

        Serializer.__init__(self, store)

    def serialize(
        self,
        stream: IO[bytes],
        base: Optional[str] = None,
        encoding: Optional[str] = "utf-8",
        **kwargs,
    ):
        if base is not None:
            warnings.warn(
                "base has no meaning for Hextuples serialization. "
                "I will ignore this value"
            )

        if encoding not in [None, "utf-8"]:
            warnings.warn(
                f"Hextuples files are always utf-8 encoded. "
                f"I was passed: {encoding}, "
                "but I'm still going to use utf-8 anyway!"
            )

        if self.store.formula_aware is True:
            raise Exception(
                "Hextuple serialization can't (yet) handle formula-aware stores"
            )
        dictionary = dict()
        result_subject = ""
        result_object = ""

        def expand_Bnode(node, g, dictionary, properties, collection_or_not):
            for s, p, o in g.triples((node, None, None)):
                #todo () and []
                # oList = properties.get(p, [])
                # oList.append(o)
                # print("atatat", s,p, o)
                # print("ptype", type(p))
                if ("http://www.w3.org/1999/02/22-rdf-syntax-ns#first" in p) or ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
                    collection_or_not  =  True
                    if o in dictionary:
                        properties.append(dictionary[o])
                    # elif isinstance(o, rdflib.term.BNode):
                    #     expand_Bnode(o, g, dictionary,properties)
                    # else:
                    #     properties.append(o)
                    elif not ("http://www.w3.org/1999/02/22-rdf-syntax-ns#nil"  in o):
                        # print("recursive", o)

                        if not ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
                            properties.append("(")

                        expand_Bnode(o, g, dictionary,properties, collection_or_not)

                        if not ("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest" in p):
                            properties.append(")")

                else:
                    collection_or_not = False
                    properties.append(p)
                    if o in dictionary:
                        properties.append(dictionary[o])
                    # elif isinstance(o, rdflib.term.BNode):
                    #     expand_Bnode(o, g, dictionary,properties)
                    # else:
                    #     properties.append(o)
                    else:
                        expand_Bnode(o, g, dictionary,properties, collection_or_not)

            return properties, collection_or_not

        for g in self.contexts:
            for s in g.subjects(predicate=RDF.type, object=RDF.Statement):
                subject = g.value(s, RDF.subject)
                predicate = g.value(s, RDF.predicate)
                object = g.value(s, RDF.object)

                # print("typetest", subject, type(subject), "\n")
                # print("current dict", dictionary, "\n")
                properties = []
                collection_or_not = False

                if isinstance(g.value(s, RDF.subject), rdflib.term.BNode):
                    if subject in dictionary:
                        subject = dictionary[g.value(s, RDF.subject)]

                if isinstance(g.value(s, RDF.object), rdflib.term.BNode):
                    if object in dictionary:
                        object = dictionary[g.value(s, RDF.object)]

                if (isinstance(subject, rdflib.term.URIRef)):
                    subject = "<"+str(subject)+">"
                elif (isinstance(subject, rdflib.term.BNode)):
                    result_subject, ifcollection = expand_Bnode(subject,g,dictionary,properties,collection_or_not)

                    if ifcollection == True:
                        result_subject.insert(0, "(")
                        result_subject.append(")")
                    else:
                        result_subject.insert(0, "[")
                        result_subject.append("]")
                    subject = "".join(result_subject)


                if (isinstance(object, rdflib.term.URIRef)):
                    object = "<"+str(object)+">"
                elif (isinstance(object, rdflib.term.BNode)):
                    result_object, ifcollection = expand_Bnode(subject,g,dictionary,properties,collection_or_not)
                    if ifcollection == True:
                        result_object.insert(0, "(")
                        result_object.append(")")
                    else:
                        result_object.insert(0, "[")
                        result_object.append("]")
                    object = "".join(result_object)

                if(isinstance(predicate, rdflib.term.URIRef)):
                    predicate = "<"+str(g.value(s, RDF.predicate))+">"

                dictionary[s] = "<< "+str(subject)+ str(predicate)+str(object)+" >>"

                output = subject+" "+predicate+" "+object+" ."+"\n"
                if output is not None:
                    stream.write(output.encode())
    #Todo


                # hl = self._hex_line(triple, context)
                # if hl is not None:
                #     stream.write(hl.encode())

    # def _hex_line(self, triple, context):
    #     if isinstance(
    #         triple[0], (URIRef, BNode)
    #     ):  # exclude QuotedGraph and other objects
    #         # value
    #         value = (
    #             triple[2]
    #             if isinstance(triple[2], Literal)
    #             else self._iri_or_bn(triple[2])
    #         )

    #         # datatype
    #         if isinstance(triple[2], URIRef):
    #             # datatype = "http://www.w3.org/1999/02/22-rdf-syntax-ns#namedNode"
    #             datatype = "globalId"
    #         elif isinstance(triple[2], BNode):
    #             # datatype = "http://www.w3.org/1999/02/22-rdf-syntax-ns#blankNode"
    #             datatype = "localId"
    #         elif isinstance(triple[2], Literal):
    #             if triple[2].datatype is not None:
    #                 datatype = f"{triple[2].datatype}"
    #             else:
    #                 if triple[2].language is not None:  # language
    #                     datatype = RDF.langString
    #                 else:
    #                     datatype = XSD.string
    #         else:
    #             return None  # can't handle non URI, BN or Literal Object (QuotedGraph)

    #         # language
    #         if isinstance(triple[2], Literal):
    #             if triple[2].language is not None:
    #                 language = f"{triple[2].language}"
    #             else:
    #                 language = ""
    #         else:
    #             language = ""

    #         return (
    #             json.dumps(
    #                 [
    #                     self._iri_or_bn(triple[0]),
    #                     triple[1],
    #                     value,
    #                     datatype,
    #                     language,
    #                     self._context(context),
    #                 ]
    #             )
    #             + "\n"
    #         )
    #     else:  # do not return anything for non-IRIs or BNs, e.g. QuotedGraph, Subjects
    #         return None

    def _iri_or_bn(self, i_):
        if isinstance(i_, URIRef):
            return f"{i_}"
        elif isinstance(i_, BNode):
            return f"{i_.n3()}"
        else:
            return None

    def _context(self, context):
        if self.graph_type == Graph:
            return ""
        if context.identifier == "urn:x-rdflib:default":
            return ""
        elif context is not None and self.default_context is not None:
            if context.identifier == self.default_context.identifier:
                return ""
        return context.identifier
