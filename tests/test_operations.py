import pytest
from decimal import Decimal
from typing import Any, Dict, Type

from app.exceptions import ValidationError
from app.operations import (
    Operation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
    Power,
    Root,
    OperationFactory,
)
#--------------------------------------------
#  Operation base class 
#--------------------------------------------

def test_operation_str_representation():
    """Verify that string representation of an operation returns its class name."""
    class TestOp(Operation):
        def execute(self, a: Decimal, b: Decimal) -> Decimal:
            return a
    assert str(TestOp()) == "TestOp"

# Updated below to use parameterized tests

#-------------------------------------------
# Addition 
#-------------------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("5",    "3",    "8"),    # positive numbers
    ("-5",   "-3",   "-8"),   # negative numbers
    ("-5",   "3",    "-2"),   # mixed signs
    ("5",    "-5",   "0"),    # zero sum
    ("5.5",  "3.3",  "8.8"), # decimals
    ("1e10", "1e10", "20000000000"),  # large numbers
])
def test_addition(a, b, expected):
    """Verify addition produces correct results across multiple input types."""
    result = Addition().execute(Decimal(a), Decimal(b))
    assert result == Decimal(expected)

#-----------------------------------------
# Subtraction 
#-----------------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("5",    "3",   "2"),           # positive numbers
    ("-5",   "-3",  "-2"),          # negative numbers
    ("-5",   "3",   "-8"),          # mixed signs
    ("5",    "5",   "0"),           # zero result
    ("5.5",  "3.3", "2.2"),         # decimals
    ("1e5",  "1e5", "0"), # large numbers
])
def test_subtraction(a, b, expected):
    """Verify subtraction produces correct results across multiple input types."""
    result = Subtraction().execute(Decimal(a), Decimal(b))
    assert result == Decimal(expected)

#---------------------------------------
#  Multiplication 
#---------------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("5",    "3",   "15"),          # positive numbers
    ("-5",   "-3",  "15"),          # negative numbers
    ("-5",   "3",   "-15"),         # mixed signs
    ("5",    "0",   "0"),           # multiply by zero
    ("5.5",  "3.3", "18.15"),       # decimals
])
def test_multiplication(a, b, expected):
    """Verify multiplication produces correct results across multiple input types."""
    result = Multiplication().execute(Decimal(a), Decimal(b))
    assert result == Decimal(expected)

#-----------------------------------
#  Division 
#-----------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("6",   "2",  "3"),    # positive numbers
    ("-6",  "-2", "3"),    # negative numbers
    ("-6",  "2",  "-3"),   # mixed signs
    ("5.5", "2",  "2.75"), # decimals
    ("0",   "5",  "0"),    # divide zero
])
def test_division_valid(a, b, expected):
    """Verify division produces correct results for valid inputs."""
    result = Division().execute(Decimal(a), Decimal(b))
    assert result == Decimal(expected)


@pytest.mark.parametrize("a, b, error, message", [
    ("5", "0", ValidationError, "Division by zero is not allowed"),
])
def test_division_invalid(a, b, error, message):
    """Verify division raises appropriate errors for invalid inputs."""
    with pytest.raises(error, match=message):
        Division().execute(Decimal(a), Decimal(b))

#----------------------------------
#  Power
#----------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("2",   "3", "8"),    # positive base and exponent
    ("5",   "0", "1"),    # zero exponent
    ("5",   "1", "5"),    # one exponent
    ("2.5", "2", "6.25"), # decimal base
    ("0",   "5", "0"),    # zero base
])
def test_power_valid(a, b, expected):
    """Verify power produces correct results for valid inputs."""
    result = Power().execute(Decimal(a), Decimal(b))
    assert result == Decimal(expected)


@pytest.mark.parametrize("a, b, error, message", [
    ("2", "-3", ValidationError, "Negative exponents not supported"),
])
def test_power_invalid(a, b, error, message):
    """Verify power raises appropriate errors for invalid inputs."""
    with pytest.raises(error, match=message):
        Power().execute(Decimal(a), Decimal(b))

#------------------------------------------
#  Root 
#------------------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("9",    "2", "3"),   # square root
    ("27",   "3", "3"),   # cube root
    ("16",   "4", "2"),   # fourth root
    ("2.25", "2", "1.5"), # decimal root
])
def test_root_valid(a, b, expected):
    """Verify root produces correct results for valid inputs."""
    result = Root().execute(Decimal(a), Decimal(b))
    assert result == Decimal(expected)


@pytest.mark.parametrize("a, b, error, message", [
    ("-9", "2", ValidationError, "Cannot calculate root of negative number"),
    ("9",  "0", ValidationError, "Zero root is undefined"),
])
def test_root_invalid(a, b, error, message):
    """Verify root raises appropriate errors for invalid inputs."""
    with pytest.raises(error, match=message):
        Root().execute(Decimal(a), Decimal(b))

#---------------------------
#  OperationFactory 
#----------------------------

@pytest.mark.parametrize("op_name, op_class", [
    ("add",      Addition),
    ("subtract", Subtraction),
    ("multiply", Multiplication),
    ("divide",   Division),
    ("power",    Power),
    ("root",     Root),
])
def test_factory_creates_valid_operations(op_name, op_class):
    """Verify factory creates the correct operation instance for each valid name."""
    assert isinstance(OperationFactory.create_operation(op_name), op_class)


@pytest.mark.parametrize("op_name, op_class", [
    ("ADD",      Addition),
    ("SUBTRACT", Subtraction),
    ("MULTIPLY", Multiplication),
    ("DIVIDE",   Division),
    ("POWER",    Power),
    ("ROOT",     Root),
])
def test_factory_case_insensitive(op_name, op_class):
    """Verify factory handles uppercase operation names correctly."""
    assert isinstance(OperationFactory.create_operation(op_name), op_class)


def test_factory_invalid_operation():
    """Verify factory raises ValueError for unknown operation names."""
    with pytest.raises(ValueError, match="Unknown operation: invalid_op"):
        OperationFactory.create_operation("invalid_op")


def test_factory_register_valid_operation():
    """Verify a new valid operation can be registered and used via the factory."""
    class NewOperation(Operation):
        def execute(self, a: Decimal, b: Decimal) -> Decimal:
            return a

    OperationFactory.register_operation("new_op", NewOperation)
    assert isinstance(OperationFactory.create_operation("new_op"), NewOperation)


def test_factory_register_invalid_operation():
    """Verify registering a class that doesn't inherit from Operation raises TypeError."""
    class InvalidOperation:
        pass

    with pytest.raises(TypeError, match="Operation class must inherit"):
        OperationFactory.register_operation("invalid", InvalidOperation)