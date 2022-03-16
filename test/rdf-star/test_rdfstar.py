"""This runs the nquads tests for the W3C RDF Working Group's N-Quads
test suite."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copyfile
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple, Union, cast
from rdflib import Graph, logger
from rdflib.namespace import Namespace, RDF, RDFS
from rdflib.term import BNode, Node, URIRef, Identifier
from rdflib.exceptions import ParserError
from rdflib.parser import Parser
from rdflib.plugin import register
from rdflib.util import guess_format
from rdfstarmanifest import RDFT, RDFTest, MF, DAWG, UP, RDFN
from test import TEST_DIR
import pytest

verbose = True

ResultType = Union[Identifier, Tuple[Identifier, List[Tuple[Identifier, Identifier]]]]
GraphDataType = Union[List[Identifier], List[Tuple[Identifier, Identifier]]]

MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
QT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")
UP = Namespace("http://www.w3.org/2009/sparql/tests/test-update#")


def read_manifest(f, base=None, legacy=False) -> Iterable[Tuple[Node, URIRef, RDFTest]]:
    def _str(x):
        if x is not None:
            return str(x)
        return None

    g = Graph()
    g.parse(f, publicID=base, format="turtle")

    for m in g.subjects(RDF.type, MF.Manifest):
        for col in g.objects(m, MF.include):
            for i in g.items(col):
                for x in read_manifest(i):
                    yield x

        for col in g.objects(m, MF.entries):
            e: URIRef
            for e in g.items(col):

                _type = g.value(e, RDF.type)

                name = g.value(e, MF.name)
                comment = g.value(e, RDFS.comment)
                data = None
                graphdata: Optional[GraphDataType] = None
                res: Optional[ResultType] = None
                syntax = True

                if _type in (MF.QueryEvaluationTest, MF.CSVResultFormatTest):
                    a = g.value(e, MF.action)
                    query = g.value(a, QT.query)
                    data = g.value(a, QT.data)
                    # NOTE: Casting to identifier because g.objects return Node
                    # but should probably return identifier instead.
                    graphdata = list(
                        cast(Iterable[Identifier], g.objects(a, QT.graphData))
                    )
                    res = g.value(e, MF.result)

                elif _type in (MF.UpdateEvaluationTest, UP.UpdateEvaluationTest):
                    a = g.value(e, MF.action)
                    query = g.value(a, UP.request)
                    data = g.value(a, UP.data)
                    graphdata = cast(List[Tuple[Identifier, Identifier]], [])
                    for gd in g.objects(a, UP.graphData):
                        graphdata.append(
                            (g.value(gd, UP.graph), g.value(gd, RDFS.label))
                        )

                    r = g.value(e, MF.result)
                    resdata: Identifier = g.value(r, UP.data)
                    resgraphdata: List[Tuple[Identifier, Identifier]] = []
                    for gd in g.objects(r, UP.graphData):
                        resgraphdata.append(
                            (g.value(gd, UP.graph), g.value(gd, RDFS.label))
                        )

                    res = resdata, resgraphdata

                elif _type in (RDFN.RDFStarTest,):
                    query = g.value(e, MF.action)
                    res = g.value(e, MF.result)
                    syntax = _type in (RDFT.TestTurtleEval, RDFT.TestTrigEval)

                else:
                    logger.debug(f"I dont know DAWG Test Type {_type}")
                    continue

                yield e, _type, RDFTest(
                    e,
                    _str(name),
                    _str(comment),
                    _str(data),
                    graphdata,
                    _str(query),
                    res,
                    syntax,
                )


def parsetest(test):
    g = Graph()
    g.parse(location=test.action, format="ttls")



testers: Dict[Node, Callable[[RDFTest], None]] = {
    RDFN.RDFStarTest: parsetest,
}


@pytest.fixture
def xfail_tests_work_in_progess(request):
    rdf_test = request.getfixturevalue("rdf_test")

    expected_failures = [
        # "nt ttl star bad syntax 1",  # test001
        # "nt ttl star bad syntax 2",  # test002
        # "nt ttl star bad syntax 3",  # test003
        # "nt ttl star bad syntax 4",  # test004
        # "nt ttl star bnode 1",  # test005
        # "nt ttl star bnode 2",  # test006
        # "nt ttl star nested 1",  # test007
        # "nt ttl star nested-2",  # test008
        # "nt ttl star syntax-1",  # test009
        # "nt ttl star syntax 2",  # test010
        # "nt ttl star syntax 3",  # test011

        # Genuine FAILs
        "nt ttl star syntax 4",  # test012
        "nt ttl star syntax 5",  # test013

        # Annotation “|” syntax NYI
        "turtle star annotation 1",  # test014
        "turtle star annotation 2",  # test015

        # "turtle star syntax bad 01",  # test016
        # "turtle star syntax bad 02",  # test017
        # "turtle star syntax bad 03",  # test018
        # "turtle star syntax bad 04",  # test019
        # "turtle star syntax bad 05",  # test020
        # "turtle star syntax bad 06",  # test021

        # Expected FAILS?
        "turtle star syntax bad 07",  # test022
        "turtle star syntax bad 08",  # test023

        # Annotation “|” syntax NYI
        "turtle star syntax bad ann 1",  # test024
        "turtle star syntax bad ann 2",  # test025

        # "turtle star syntax basic 01",  # test026
        # "turtle star syntax basic 02",  # test027
        # "turtle star syntax bnode 01",  # test028
        # "turtle star syntax bnode 02",  # test029
        # "turtle star syntax bnode 03",  # test030
        # "turtle star syntax compound",  # test031
        # "turtle star syntax inside 01",  # test032
        # "turtle star syntax inside 02",  # test033
        # "turtle star syntax nested 01",  # test034
        # "turtle star syntax nested 02",  # test035
    ]
    if rdf_test.name in expected_failures:
        request.node.add_marker(
            pytest.mark.xfail(reason=f"Expected failure for {rdf_test.name}")
        )

@pytest.mark.parametrize(
    "rdf_test_uri, type, rdf_test",
    read_manifest(os.path.join(TEST_DIR, "rdf-star/turtle-star/manifest-rdfstar.ttl")),
)
@pytest.mark.usefixtures("xfail_tests_work_in_progess")
def test_rdfstar_manifest(rdf_test_uri: URIRef, type: Node, rdf_test: RDFTest):
    testers[type](rdf_test)
