from pipeline.analyze import _extract_json_object


def test_extract_json_object_from_plain_text():
    assert _extract_json_object('prefix {"mode": "search"} suffix') == {"mode": "search"}


def test_extract_json_object_from_fenced_json():
    raw = """```json
    {"mode": "parametric", "sub_queries": ["hi"]}
    ```"""

    assert _extract_json_object(raw) == {"mode": "parametric", "sub_queries": ["hi"]}


def test_extract_json_object_returns_none_for_invalid_json():
    assert _extract_json_object("not json") is None
    assert _extract_json_object("{bad json}") is None
