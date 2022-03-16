"""
SImple test of SPARQL Star recursion
"""
import pytest
import os
from test import TEST_DIR
from rdflib import Graph, URIRef, logger

def test_sample():
    g = Graph()

    with open(os.path.join(TEST_DIR + "/rdf-star", "sample.ttl"), 'r') as fp:
        data = fp.read()
    g.parse(data=data, format='ttls', publicID=URIRef("http://example.org"))

    res = g.query(
        "SELECT ?s1 WHERE{<<<<?s1 ?p1 ?o1>> ?p2 ?o2>> ?p3 ?o3.}"
    )

    for row in res:
        assert row["s1"] == URIRef('http://example.org/Story')
