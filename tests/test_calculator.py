import pytest

from pipeline.tools.calculator import CalculatorError, evaluate_expression


def test_evaluate_expression_allows_basic_arithmetic():
    calc = evaluate_expression("(340 * 0.15) + (48 / 6) ** 2")

    assert calc.result == 115
    assert calc.answer_text == "115"


def test_evaluate_expression_rejects_calls_and_names():
    with pytest.raises(CalculatorError):
        evaluate_expression("__import__('os').system('echo bad')")

    with pytest.raises(CalculatorError):
        evaluate_expression("price * 0.15")


def test_evaluate_expression_rejects_division_by_zero_and_huge_power():
    with pytest.raises(CalculatorError):
        evaluate_expression("1 / 0")

    with pytest.raises(CalculatorError):
        evaluate_expression("2 ** 99")
