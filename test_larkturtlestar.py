from test.data import context0

import pytest

import rdflib
from rdflib.compare import isomorphic

rdflib.plugin.register(
    "larkturtlestar",
    rdflib.parser.Parser,
    "rdflib.experimental.plugins.parsers.larkturtlestar",
    "LarkTurtleStarParser",
)

rdflib.plugin.register(
    "larkntstar",
    rdflib.parser.Parser,
    "rdflib.experimental.plugins.parsers.larkntriplesstar",
    "LarkNTriplesStarParser",
)

rdflib.plugin.register(
    "rdna",
    rdflib.serializer.Serializer,
    "rdflib.plugins.serializers.rdna",
    "RDNASerializer",
)


import pytest
import sys
from rdflib import Graph
from pympler import asizeof
import time
from objsize import get_deep_size
# tests should be past
current = time.time()
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-basic-01.ttl", format = "larkturtlestar")
# print(asizeof.asizeof(g))
print(get_deep_size(g))
counter = 1
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-basic-02.ttl", format = "larkturtlestar")
# print(asizeof.asizeof(g))
print(get_deep_size(g))
counter+=1
size = 0
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-inside-01.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-inside-02.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-nested-01.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-nested-02.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-compound.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-bnode-01.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-bnode-02.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-syntax-bnode-03.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-annotation-1.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-annotation-2.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-syntax-1.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-syntax-2.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-syntax-3.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-syntax-4.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-syntax-5.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-bnode-1.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-bnode-2.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-nested-1.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/nt-ttl-star-nested-2.ttl" , format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-01.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-02.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-bnode-1.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-bnode-2.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-annotation-1.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-annotation-2.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-annotation-3.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-annotation-4.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-annotation-5.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-quoted-annotation-1.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-quoted-annotation-2.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
g = Graph()
g.parse("test/test_rdfstar/efficiency-turtlestar/turtle-star-eval-quoted-annotation-3.ttl", format = "larkturtlestar")
print(get_deep_size(g))
counter+=1
size+=get_deep_size(g)
end = time.time()
print(counter, size, end - current)
