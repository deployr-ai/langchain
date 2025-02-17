from typing import Any, Dict, Tuple

import pytest

from langchain.chains.query_constructor.ir import (Comparator, Comparison,
                                                   Operation, Operator,
                                                   StructuredQuery)
from langchain.retrievers.self_query.myscale import MyScaleTranslator

DEFAULT_TRANSLATOR = MyScaleTranslator()


@pytest.mark.parametrize(
    "triplet",
    [
        (Comparator.LT, 2, "metadata.foo < 2"),
        (Comparator.LTE, 2, "metadata.foo <= 2"),
        (Comparator.GT, 2, "metadata.foo > 2"),
        (Comparator.GTE, 2, "metadata.foo >= 2"),
        (Comparator.CONTAIN, 2, "has(metadata.foo,2)"),
        (Comparator.LIKE, "bar", "metadata.foo ILIKE '%bar%'"),
    ],
)
def test_visit_comparison(triplet: Tuple[Comparator, Any, str]) -> None:
    comparator, value, expected = triplet
    comp = Comparison(comparator=comparator, attribute="foo", value=value)
    actual = DEFAULT_TRANSLATOR.visit_comparison(comp)
    assert expected == actual


def test_visit_operation() -> None:
    op = Operation(
        operator=Operator.AND,
        arguments=[
            Comparison(comparator=Comparator.LT, attribute="foo", value=2),
            Comparison(comparator=Comparator.EQ, attribute="bar", value="baz"),
        ],
    )
    expected = "metadata.foo < 2 AND metadata.bar = 'baz'"
    actual = DEFAULT_TRANSLATOR.visit_operation(op)
    assert expected == actual


def test_visit_structured_query() -> None:
    query = "What is the capital of France?"
    structured_query = StructuredQuery(
        query=query,
        filter=None,
    )
    expected: Tuple[str, Dict] = (query, {})
    actual = DEFAULT_TRANSLATOR.visit_structured_query(structured_query)
    assert expected == actual

    comp = Comparison(comparator=Comparator.LT, attribute="foo", value=["1", "2"])
    structured_query = StructuredQuery(
        query=query,
        filter=comp,
    )
    expected = (
        query,
        {"where_str": "metadata.foo < ['1', '2']"},
    )
    actual = DEFAULT_TRANSLATOR.visit_structured_query(structured_query)
    assert expected == actual

    op = Operation(
        operator=Operator.AND,
        arguments=[
            Comparison(comparator=Comparator.LT, attribute="foo", value=2),
            Comparison(comparator=Comparator.EQ, attribute="bar", value="baz"),
        ],
    )
    structured_query = StructuredQuery(
        query=query,
        filter=op,
    )
    expected = (
        query,
        {"where_str": "metadata.foo < 2 AND metadata.bar = 'baz'"},
    )
    actual = DEFAULT_TRANSLATOR.visit_structured_query(structured_query)
    assert expected == actual
