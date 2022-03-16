
import pytest
import os
from rdflib import Graph
from test import TEST_DIR

# tests should be past
def test_TurtlePositiveSyntax_subject():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-basic-01.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_object():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-basic-02.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_quotedtripleinsideblankNodePropertyList():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-inside-01.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_quotedtripleinsidecollection():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-inside-02.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_nestedquotedtriplesubjectposition():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-nested-01.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_nestedquotedtripleobjectposition():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-nested-02.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_compoundforms():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-compound.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_blanknodesubject():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bnode-01.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_blanknodeobject():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bnode-02.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_blanknode():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bnode-03.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Annotation syntax not yet implemented")
def test_TurtlePositiveSyntax_Annotationform():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-annotation-1.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Annotation syntax not yet implemented")
def test_TurtlePositiveSyntax_Annotationexample():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-annotation-2.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_subjectquotedtriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-syntax-1.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_objectquotedtriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-syntax-2.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_subjectandobjectquotedtriples():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-syntax-3.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Unexpected FAIL")
def test_TurtlePositiveSyntax_whitespaceandterms():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-syntax-4.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Unexpected FAIL")
def test_TurtlePositiveSyntax_Nestednowhitespace():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-syntax-5.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_Blanknodesubject():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-bnode-1.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_Blanknodeobject():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-bnode-2.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_Nestedsubjectterm1():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-nested-1.ttl"), format = "ttls")

def test_TurtlePositiveSyntax_Nestedsubjectterm2():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-nested-2.ttl"), format = "ttls")

# tests should be broken

@pytest.mark.xfail(reason="Bad quoted triple literal subject")
def test_TurtleNegativeSyntax_Badquotedtripleliteralsubject1():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-bad-syntax-1.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Bad quoted triple literal subject")
def test_TurtleNegativeSyntax_Badquotedtripleliteralsubject2():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-bad-syntax-2.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Badquotedtripleliteralpredicate")
def test_TurtleNegativeSyntax_Badquotedtripleliteralpredicate3():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-bad-syntax-3.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Badquotedtripleblanknodepredicate")
def test_TurtleNegativeSyntax_Badquotedtripleblanknodepredicate():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/nt-ttl-star-bad-syntax-4.ttl"), format = "ttls")

@pytest.mark.xfail(reason="Badquotedtripleblanknodepredicate")
def test_TurtleNegativeSyntax_badquotedtripleaspredicate():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-01.ttl"), format = "ttls")

@pytest.mark.xfail(reason="badquotedtripleoutsidetriple")
def test_TurtleNegativeSyntax_badquotedtripleoutsidetriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-02.ttl"), format = "ttls")

@pytest.mark.xfail(reason="collectionlistinquotedtriple")
def test_TurtleNegativeSyntax_collectionlistinquotedtriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-03.ttl"), format = "ttls")

@pytest.mark.xfail(reason="badliteralinsubjectpositionofquotedtriple")
def test_TurtleNegativeSyntax_badliteralinsubjectpositionofquotedtriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-04.ttl"), format = "ttls")

@pytest.mark.xfail(reason="blanknodeaspredicateinquotedtriple")
def test_TurtleNegativeSyntax_blanknodeaspredicateinquotedtriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-05.ttl"), format = "ttls")

@pytest.mark.xfail(reason="compoundblanknodeexpression")
def test_TurtlePositiveSyntax_compoundblanknodeexpression():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-06.ttl"), format = "ttls")

@pytest.mark.xfail(reason="ncompletequotetriple")
def test_TurtlePositiveSyntax_ncompletequotetriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-07.ttl"), format = "ttls")

@pytest.mark.xfail(reason="overlongquotedtriple")
def test_TurtlePositiveSyntax_overlongquotedtriple():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-08.ttl"), format = "ttls")

@pytest.mark.xfail(reason="emptyannotation")
def test_TurtlePositiveSyntax_emptyannotation():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-ann-1.ttl"), format = "ttls")

@pytest.mark.xfail(reason="tripleasannotation")
def test_TurtlePositiveSyntax_tripleasannotation():
    g = Graph()
    g.parse(location=os.path.join(TEST_DIR + "/rdf-star", "turtle-star/turtle-star-syntax-bad-ann-2.ttl"), format = "ttls")
