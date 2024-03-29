"""
Trig RDF graph serializer for RDFLib.
See <http://www.w3.org/TR/trig/> for syntax specification.
"""

from collections import defaultdict
from typing import IO, TYPE_CHECKING, Optional, Union

from rdflib.graph import ConjunctiveGraph, Graph
from rdflib.plugins.serializers.turtle import TurtleSerializer
from rdflib.term import BNode, Node


__all__ = ["TrigSerializer"]


class TrigSerializer(TurtleSerializer):

    short_name = "trig"
    indentString = 4 * " "

    def __init__(self, store: Union[Graph, ConjunctiveGraph]):
        print("init", list(store.contexts()))
        self.default_context: Optional[Node]
        if store.context_aware:
            if TYPE_CHECKING:
                assert isinstance(store, ConjunctiveGraph)
            self.contexts = list(store.contexts())
            self.default_context = store.default_context.identifier
            if store.default_context:
                self.contexts.append(store.default_context)
        else:
            self.contexts = [store]
            self.default_context = None

        super(TrigSerializer, self).__init__(store)

    def preprocess(self):
        for context in self.contexts:
            self.store = context
            self.getQName(context.identifier)
            self._references = defaultdict(int)
            self._subjects = {}

            for triple in context:
                self.preprocessTriple(triple)

            self._contexts[context] = (
                self.orderSubjects(),
                self._subjects,
                self._references,
            )

    def reset(self):
        super(TrigSerializer, self).reset()
        self._contexts = {}

    def serialize(
        self,
        stream: IO[bytes],
        base: Optional[str] = None,
        encoding: Optional[str] = None,
        spacious: Optional[bool] = None,
        **args,
    ):
        self.reset()
        self.stream = stream
        # if base is given here, use that, if not and a base is set for the graph use that
        if base is not None:
            self.base = base
        elif self.store.base is not None:
            self.base = self.store.base

        if spacious is not None:
            self._spacious = spacious

        self.preprocess()

        self.startDocument()
        print("start\n\n\n\n\n")
        firstTime = True
        print("start\n\n\n\n\ndasdasd", self._contexts.items())
        for store, (ordered_subjects, subjects, ref) in self._contexts.items():
            if not ordered_subjects:
                continue
            print(store, (ordered_subjects, subjects, ref))
            self._references = ref
            self._serialized = {}
            self.store = store
            self._subjects = subjects

            if self.default_context and store.identifier == self.default_context:
                self.write(self.indent() + "\n{")
            else:
                print("asdadsdasd", store.identifier)
                iri: Optional[str]
                if isinstance(store.identifier, BNode):
                    iri = store.identifier.n3()
                else:
                    iri = self.getQName(store.identifier)
                    if iri is None:
                        iri = store.identifier.n3()
                self.write(self.indent() + "\n%s {" % iri)

            self.depth += 1
            for subject in ordered_subjects:
                if self.isDone(subject):
                    continue
                if firstTime:
                    firstTime = False
                if self.statement(subject) and not firstTime:
                    self.write("\n")
            self.depth -= 1
            self.write("}\n")

        self.endDocument()
        stream.write("\n".encode("latin-1"))
