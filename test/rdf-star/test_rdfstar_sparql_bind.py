import pytest
import os
from test import TEST_DIR
from rdflib import Graph, URIRef, logger

"""
A simple example showing how to process Bind over Sparql Star format query
"""

def test_sample():
    g = Graph()

    with open(os.path.join(TEST_DIR + "/rdf-star", "sample.ttl"), 'r') as fp:
        data = fp.read()
    g.parse(data=data, format='ttls', publicID=URIRef("http://example.org"))

    res = g.query("""SELECT ?x WHERE{ <<?s ?p ?o>> ?p1 ?o1 . BIND(<<?s ?p ?o>> AS ?x)}""")

    for row in res:
        assert row["x"] in [
            URIRef('http://www.w3.org/2002/07/owl#Par'),
            URIRef('http://www.w3.org/2002/07/owl#st'),
        ]
