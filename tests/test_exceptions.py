import pytest
from app.exceptions import CalculatorError, ValidationError, OperationError, ConfigurationError


# Updated below to use parameterized tests

#--------------------------------------
#  Inheritance tests
#--------------------------------------

@pytest.mark.parametrize("exception_class, message", [
    (ValidationError,    "Validation failed"),
    (OperationError,     "Operation failed"),
    (ConfigurationError, "Configuration invalid"),
])
def test_error_inherits_from_calculator_error(exception_class, message):
    """Verify that all custom exceptions inherit from CalculatorError."""
    with pytest.raises(CalculatorError) as exc_info:
        raise exception_class(message)
    assert isinstance(exc_info.value, CalculatorError)
    assert str(exc_info.value) == message

#----------------------------------------
#  Base exception test 
#----------------------------------------

def test_calculator_error_is_base_exception():
    """Verify CalculatorError can be raised and caught as a base exception."""
    with pytest.raises(CalculatorError) as exc_info:
        raise CalculatorError("Base calculator error occurred")
    assert str(exc_info.value) == "Base calculator error occurred"

#----------------------------------------
#  Specific exception tests 
#----------------------------------------

@pytest.mark.parametrize("exception_class, message", [
    (ValidationError,    "Validation error"),
    (OperationError,     "Specific operation error"),
    (ConfigurationError, "Specific configuration error"),
])
def test_specific_exception_caught_directly(exception_class, message):
    """Verify each exception can be raised and caught by its own type."""
    with pytest.raises(exception_class) as exc_info:
        raise exception_class(message)
    assert str(exc_info.value) == message