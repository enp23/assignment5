import pytest
from decimal import Decimal
from datetime import datetime
from app.calculation import Calculation
from app.exceptions import OperationError
import logging

# Updated below to parameterized tests

#------------------------------------------------------
# Valid arithmetic operations
#------------------------------------------------------

@pytest.mark.parametrize("operation, operand1, operand2, expected", [
    ("Addition",       "2",  "3",  "5"),   # basic addition
    ("Subtraction",    "5",  "3",  "2"),   # basic subtraction
    ("Multiplication", "4",  "2",  "8"),   # basic multiplication
    ("Division",       "8",  "2",  "4"),   # basic division
    ("Power",          "2",  "3",  "8"),   # basic power
    ("Root",           "16", "2",  "4"),   # basic root
])
def test_valid_operations(operation, operand1, operand2, expected):
    """Verify that valid arithmetic operations produce the correct result."""
    calc = Calculation(
        operation=operation,
        operand1=Decimal(operand1),
        operand2=Decimal(operand2)
    )
    assert calc.result == Decimal(expected)


#------------------------------------------------------
# Invalid arithmetic operations
#------------------------------------------------------

@pytest.mark.parametrize("operation, operand1, operand2, error, message", [
    ("Division", "8",      "0",      OperationError, "Division by zero is not allowed"),
    ("Power",    "2",      "-3",     OperationError, "Negative exponents are not supported"),
    ("Root",     "-16",    "2",      OperationError, "Cannot calculate root of negative number"),
    ("Unknown",  "5",      "3",      OperationError, "Unknown operation"),
    ("Power",    "999999", "999999", OperationError, "Calculation failed"),
])
def test_invalid_operations(operation, operand1, operand2, error, message):
    """Verify that invalid operations raise appropriate errors during initialization."""
    with pytest.raises(error, match=message):
        Calculation(
            operation=operation,
            operand1=Decimal(operand1),
            operand2=Decimal(operand2)
        )


#------------------------------------------------------
# to_dict and from_dict
#------------------------------------------------------

def test_to_dict():
    """Verify that to_dict returns a correctly structured dictionary."""
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    result_dict = calc.to_dict()
    assert result_dict == {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": calc.timestamp.isoformat()
    }


def test_from_dict():
    """Verify that from_dict correctly reconstructs a Calculation from a dictionary."""
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    calc = Calculation.from_dict(data)
    assert calc.operation == "Addition"
    assert calc.operand1 == Decimal("2")
    assert calc.operand2 == Decimal("3")
    assert calc.result == Decimal("5")


def test_invalid_from_dict():
    """Verify that from_dict raises OperationError when data is invalid."""
    data = {
        "operation": "Addition",
        "operand1": "invalid",
        "operand2": "3",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)


def test_from_dict_result_mismatch(caplog):
    """
    Verify that from_dict logs a warning when the saved result
    does not match the computed result.
    """
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "10",
        "timestamp": datetime.now().isoformat()
    }
    with caplog.at_level(logging.WARNING):
        calc = Calculation.from_dict(data)
    assert "Loaded calculation result 10 differs from computed result 5" in caplog.text


#------------------------------------------------------
# Format result
#------------------------------------------------------

@pytest.mark.parametrize("precision, expected", [
    (2,  "0.33"),
    (10, "0.3333333333"),
])
def test_format_result(precision, expected):
    """Verify that format_result returns the correct string for different precisions."""
    calc = Calculation(operation="Division", operand1=Decimal("1"), operand2=Decimal("3"))
    assert calc.format_result(precision=precision) == expected


#------------------------------------------------------
# Equality
#------------------------------------------------------

def test_equality():
    """Verify that two identical Calculation objects are equal."""
    calc1 = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    calc2 = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    calc3 = Calculation(operation="Subtraction", operand1=Decimal("5"), operand2=Decimal("3"))
    assert calc1 == calc2
    assert calc1 != calc3


def test_equality_with_non_calculation():
    """
    Verify that comparing a Calculation object to a non-Calculation
    object returns NotImplemented, resulting in inequality.
    """
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    assert calc != "not a calculation"


#------------------------------------------------------
# String representations
#------------------------------------------------------

def test_str_representation():
    """
    Verify that str() returns a human-readable string showing
    the operation and operands in the expected format.
    """
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    assert str(calc) == "Addition(2, 3) = 5"


def test_repr():
    """
    Verify that repr() returns a detailed string representation
    of the Calculation object containing all attributes.
    """
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    result = repr(calc)
    assert "Addition" in result
    assert "2" in result
    assert "3" in result