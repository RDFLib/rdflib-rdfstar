"""
Code for tying SPARQL Engine into RDFLib

These should be automatically registered with RDFLib

"""

from rdflib.plugins.sparql.rdfstarpreprocessing import Preprocessingqueryintordfstar
from rdflib.query import Processor, Result, UpdateProcessor

from rdflib.plugins.sparql.sparql import Query

from rdflib.plugins.sparql.parser import parseQuery, parseUpdate
from rdflib.plugins.sparql.algebra import translateQuery, translateUpdate

from rdflib.plugins.sparql.evaluate import evalQuery
from rdflib.plugins.sparql.update import evalUpdate


def prepareQuery(queryString, initNs={}, base=None) -> Query:
    """
    Parse and translate a SPARQL Query
    """
    ret = translateQuery(parseQuery(queryString), base, initNs)
    ret._original_args = (queryString, initNs, base)
    return ret


def prepareUpdate(updateString, initNs={}, base=None):
    """
    Parse and translate a SPARQL Update
    """
    ret = translateUpdate(parseUpdate(updateString), base, initNs)
    ret._original_args = (updateString, initNs, base)
    return ret


def processUpdate(graph, updateString, initBindings={}, initNs={}, base=None):
    """
    Process a SPARQL Update Request
    returns Nothing on success or raises Exceptions on error
    """
    evalUpdate(
        graph, translateUpdate(parseUpdate(updateString), base, initNs), initBindings
    )


class SPARQLResult(Result):
    def __init__(self, res):
        Result.__init__(self, res["type_"])
        self.vars = res.get("vars_")
        self.bindings = res.get("bindings")
        self.askAnswer = res.get("askAnswer")
        self.graph = res.get("graph")


class SPARQLUpdateProcessor(UpdateProcessor):
    def __init__(self, graph):
        self.graph = graph

    def update(self, strOrQuery, initBindings={}, initNs={}):
        if isinstance(strOrQuery, str):
            strOrQuery = translateUpdate(parseUpdate(strOrQuery), initNs=initNs)

        return evalUpdate(self.graph, strOrQuery, initBindings)


class SPARQLProcessor(Processor):
    def __init__(self, graph):
        self.graph = graph

    def query(self, strOrQuery, initBindings={}, initNs={}, base=None, DEBUG=False):
        """
        Evaluate a query with the given initial bindings, and initial
        namespaces. The given base is used to resolve relative URIs in
        the query and will be overridden by any BASE given in the query.
        """

        if not isinstance(strOrQuery, Query):
            print("sparql", Preprocessingqueryintordfstar(strOrQuery))
            strOrQuery = Preprocessingqueryintordfstar(strOrQuery)
            parsetree = parseQuery(strOrQuery)
            print("test1", parsetree)
            query = translateQuery(parsetree, base, initNs)
            print("test2", query)
        else:
            query = strOrQuery
        return evalQuery(self.graph, query, initBindings, base)
