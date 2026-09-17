from app.models import StructuredQuery


def test_list_queries_default_to_the_safe_output_cap() -> None:
    assert StructuredQuery(operation="list").limit == 100
