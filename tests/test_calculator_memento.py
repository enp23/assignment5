import pytest
from decimal import Decimal
from app.calculator_memento import CalculatorMemento
from app.calculation import Calculation

#------------------------------------------------------
# Memento Tests
#------------------------------------------------------

# added to cover calculator_memento.py line 34
def test_memento_to_dict():
    """
    Verify that to_dict correctly serializes a CalculatorMemento instance
    into a dictionary containing history and timestamp keys.
    """
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    memento = CalculatorMemento(history=[calc])
    data = memento.to_dict()
    assert 'history' in data
    assert 'timestamp' in data
    assert data['history'][0]['operation'] == 'Addition'

# added to cover calculator_memento.py line 53
def test_memento_from_dict():
    """
    Verify that from_dict correctly deserializes a dictionary back into
    a CalculatorMemento instance with the original history restored.
    """
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    memento = CalculatorMemento(history=[calc])
    data = memento.to_dict()
    restored = CalculatorMemento.from_dict(data)
    assert len(restored.history) == 1
    assert restored.history[0].operation == 'Addition'
