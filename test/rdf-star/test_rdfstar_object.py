import pytest
from rdflib import Graph, URIRef, logger

"""
To test for Rdf* graphs with embedded Triples as the object rather than subject
equivalent to
Reification of the object, rather than subject.
"""

rdf_graph = """
    PREFIX ex:<http://example.org/>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:<http://xmlns.com/foaf/0.1/>
    PREFIX dct:<http://purl.org/dc/terms/>

    ex:bob foaf:name "Bob" ;
            foaf:age 23 .
    _:s rdf:type rdf:Statement ;
    rdf:subject ex:bob ;
    rdf:predicate foaf:age ;
    rdf:object 23 .

    ex:PeopleInfo dct:isSourceOf _:s ;
        ex:hasURL <http://example.com/crawlers#c1> .

    ex:welles foaf:name "John Welles" ;
                ex:mentioned ex:kubrick .
    ex:kubrick foaf:name "Stanley Kubrick" ;
                ex:influencedBy ex:welles .
    _:s1 rdf:type rdf:Statement ;
    rdf:subject ex:kubrick ;
    rdf:predicate ex:influencedBy ;
    rdf:object ex:welles .

    _:s1 dct:creator <http://example.com/names#examples> ;
        dct:source <http://example.net/people.html> .

    """

sparql_query = """
    PREFIX ex:<http://example.org/>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:<http://xmlns.com/foaf/0.1/>
    PREFIX dct:<http://purl.org/dc/terms/>

    SELECT ?x ?src WHERE {
    {?x foaf:age ?age .
    ?r rdf:type rdf:Statement ;
    rdf:subject ?x ;
    rdf:predicate foaf:age ;
    rdf:object ?age .
    ex:PeopleInfo dct:isSourceOf ?r ;
    ex:hasURL ?src .}
    UNION {
    ?x ex:influencedBy ?y .
    ?r2 rdf:type rdf:Statement ;
    rdf:subject ?x ;
    rdf:predicate ex:influencedBy ;
    rdf:object ?y ;
    dct:source ?src .}
    }
"""

rdf_star_graph = """
    PREFIX ex:<http://example.org/>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:<http://xmlns.com/foaf/0.1/>
    PREFIX dct:<http://purl.org/dc/terms/>

    ex:bob foaf:name "Bob" .
    ex:PeopleInfo dct:isSourceOf <<ex:bob foaf:age 23>> ;
        ex:hasURL <http://example.com/crawlers#c1> .

    ex:welles foaf:name "John Welles" ;
                ex:mentioned ex:kubrick .
    ex:kubrick foaf:name "Stanley Kubrick" .
    <<ex:kubrick ex:influencedBy ex:welles>> dct:creator <http://example.com/names#examples> ;
    dct:source <http://example.net/people.html> .

"""

sparql_star_query = """
    PREFIX ex:<http://example.org/>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:<http://xmlns.com/foaf/0.1/>
    PREFIX dct:<http://purl.org/dc/terms/>

    SELECT ?x ?age ?src WHERE {
    {
    ex:PeopleInfo dct:isSourceOf <<?x foaf:age ?age>> ;
    ex:hasURL ?src . }
    UNION
    { <<?x ex:influencedBy ?y>> dct:source ?src . }
    }

"""


def test_rdf_basic():
    g = Graph()
    g.parse(data=rdf_graph, format="ttl")
    for row in g.query(sparql_query):
        assert row["x"] in [
            URIRef('http://example.org/bob'),
            URIRef('http://example.org/kubrick')
        ]
        assert row["src"] in [
            URIRef('http://example.com/crawlers#c1'),
            URIRef('http://example.net/people.html')
        ]

    for row in g.query(sparql_star_query):
        assert row["x"] in [
            URIRef('http://example.org/bob'),
            URIRef('http://example.org/kubrick')
        ]
        assert row["src"] in [
            URIRef('http://example.com/crawlers#c1'),
            URIRef('http://example.net/people.html')
        ]


def test_rdf_star():
    g = Graph()
    g.parse(data=rdf_star_graph, format="ttls")

    for row in g.query(sparql_query):
        assert row["x"] in [
            URIRef('http://example.org/bob'),
            URIRef('http://example.org/kubrick')
        ]
        assert row["src"] in [
            URIRef('http://example.com/crawlers#c1'),
            URIRef('http://example.net/people.html')
        ]

    for row in g.query(sparql_star_query):
        assert row["x"] in [
            URIRef('http://example.org/bob'),
            URIRef('http://example.org/kubrick')
        ]
        assert row["src"] in [
            URIRef('http://example.com/crawlers#c1'),
            URIRef('http://example.net/people.html')
        ]

