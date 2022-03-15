"""This runs the nquads tests for the W3C RDF Working Group's N-Quads
test suite."""
import pytest
from rdflib import Graph, Literal, URIRef


"""
A very basic Rdf Star graph with only 1 embedded triple as Subject.
"""


rdf_graph = """PREFIX ex: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>

ex:bob foaf:name "Bob" ;
foaf:age 23 .
_:s1 rdf:type rdf:Statement ;
rdf:subject ex:bob ;
rdf:predicate foaf:age ;
rdf:object 23 .

_:s1 dct:creator <http://example.com/crawlers#c1> ;
    dct:source <http://example.net/listing.html> .

"""

sparql_query = """PREFIX ex: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?x ?age ?src WHERE {
?x foaf:age ?age .
?r rdf:type rdf:Statement ;
rdf:subject ?x ;
rdf:predicate foaf:age ;
rdf:object ?age ;
dct:source ?src . }
"""

rdf_star_graph = """PREFIX ex: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>

ex:bob foaf:name "Bob" .
<<ex:bob foaf:age 23>> dct:creator <http://example.com/crawlers#c1> ;
dct:source <http://example.net/listing.html> .
"""

sparql_star_query = """PREFIX ex: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?x ?age ?src WHERE { <<?x foaf:age ?age>> dct:source ?src . }
"""

def test_rdf_graph():
    g = Graph()
    g.bind("ex", URIRef("http://example.org/"))
    g.parse(data=rdf_graph, format="ttl")

    for row in g.query(sparql_query):
        assert row["x"] == URIRef('http://example.org/bob')
        assert row["age"] == Literal('23', datatype=URIRef('http://www.w3.org/2001/XMLSchema#integer'))

    for row in g.query(sparql_star_query):
        assert row["x"] == URIRef('http://example.org/bob')
        assert row["age"] == Literal('23', datatype=URIRef('http://www.w3.org/2001/XMLSchema#integer'))


def test_rdf_star():
    g = Graph()
    g.bind("ex", URIRef("http://example.org/"))
    g.parse(data=rdf_star_graph, format="ttls")

    for row in g.query(sparql_query):
        assert row["x"] == URIRef('http://example.org/bob')
        assert row["age"] == Literal('23', datatype=URIRef('http://www.w3.org/2001/XMLSchema#integer'))

    for row in g.query(sparql_star_query):
        assert row["x"] == URIRef('http://example.org/bob')
        assert row["age"] == Literal('23', datatype=URIRef('http://www.w3.org/2001/XMLSchema#integer'))
