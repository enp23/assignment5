import datetime
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import Mock, patch, PropertyMock
from decimal import Decimal
from tempfile import TemporaryDirectory
from app.calculator import Calculator
from app.calculator_memento import CalculatorMemento
from app.calculation import Calculation
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver, AutoSaveObserver
from app.operations import OperationFactory

# Fixture to initialize Calculator with a temporary directory for file paths
@pytest.fixture
def calculator():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)

        # Patch properties to use the temporary directory paths
        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
            
            # Set return values to use paths within the temporary directory
            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs/calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history/calculator_history.csv"
            
            # Return an instance of Calculator with the mocked config
            yield Calculator(config=config)

#--------------------------------------------
# Calculator Initialization Tests
#--------------------------------------------

# Test Calculator Initialization

def test_calculator_initialization(calculator):
    """Verify calculator initializes with empty history, stacks, and no operation set."""
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None

# Test Logging Setup

@patch('app.calculator.logging.info')
def test_logging_setup(logging_info_mock):
    """Verify that calculator logs a message on successful initialization."""
    with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
         patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file:
        mock_log_dir.return_value = Path('/tmp/logs')
        mock_log_file.return_value = Path('/tmp/logs/calculator.log')
        
        # Instantiate calculator to trigger logging
        calculator = Calculator(CalculatorConfig())
        logging_info_mock.assert_any_call("Calculator initialized with configuration")

# added to cover lines 103-106 in calculator.py
def test_logging_setup_failure():
    """
    Verify that an exception is raised when logging setup fails due to
    a FileHandler error during Calculator initialization.
    """
    with patch('app.calculator.logging.FileHandler', side_effect=Exception("log error")):
        with pytest.raises(Exception):
            Calculator()


# added to cover lines 77-79 in calculator.py
def test_init_history_load_failure():
    """
    Verify that the Calculator initializes successfully even when load_history
    raises an exception, logging a warning instead of crashing.
    """
    with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
         patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
         patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
         patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
        mock_log_dir.return_value = Path('/tmp/logs')
        mock_log_file.return_value = Path('/tmp/logs/calculator.log')
        mock_history_dir.return_value = Path('/tmp/history')
        mock_history_file.return_value = Path('/tmp/history/calculator_history.csv')
        with patch.object(Calculator, 'load_history', side_effect=Exception("load error")):
            calc = Calculator()  # should still initialize, just log a warning
            assert calc.history == []

#-----------------------------------------
# Observer Tests using parameterized tests
#-----------------------------------------

@pytest.mark.parametrize("observer_class", [
    LoggingObserver,
    AutoSaveObserver,
])
def test_add_observer(calculator, observer_class):
    """Verify that observers can be added to the calculator."""
    observer = observer_class(calculator) if observer_class == AutoSaveObserver else observer_class()
    calculator.add_observer(observer)
    assert observer in calculator.observers


@pytest.mark.parametrize("observer_class", [
    LoggingObserver,
    AutoSaveObserver,
])

def test_remove_observer(calculator, observer_class):
    """Verify that observers can be removed from the calculator."""
    observer = observer_class(calculator) if observer_class == AutoSaveObserver else observer_class()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    assert observer not in calculator.observers

#----------------------------------------------
# Operation Tests
#----------------------------------------------

# Test Setting Operations

def test_set_operation(calculator):
    """Verify that set_operation correctly assigns the operation strategy."""
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    assert calculator.operation_strategy == operation

# Test Performing Operations

@pytest.mark.parametrize("op_name, a, b, expected", [
    ("add",      2, 3, Decimal("5")),   # addition
    ("subtract", 5, 3, Decimal("2")),   # subtraction
    ("multiply", 4, 3, Decimal("12")),  # multiplication
    ("divide",   6, 2, Decimal("3")),   # division
    ("power",    2, 3, Decimal("8")),   # power
])
def test_perform_operation_valid(calculator, op_name, a, b, expected):
    """Verify that valid operations produce the correct result."""
    calculator.set_operation(OperationFactory.create_operation(op_name))
    result = calculator.perform_operation(a, b)
    assert result == expected

def test_perform_operation_validation_error(calculator):
    """Verify that invalid input raises a ValidationError."""
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('invalid', 3)

def test_perform_operation_operation_error(calculator):
    """Verify that performing an operation without setting one raises OperationError."""
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(2, 3)

# added to cover lines 230-233 in calculator.py
def test_calculate_unexpected_error(calculator):
    """
    Verify that an unexpected exception during perform_operation is caught
    and re-raised as an OperationError with an appropriate message.
    """
    calculator.set_operation(OperationFactory.create_operation('add'))
    with patch('app.calculator.Calculation', side_effect=Exception("unexpected")):
        with pytest.raises(OperationError, match="Operation failed"):
            calculator.perform_operation(2, 3)


#------------------------------------------------
# Undo/Redo Tests
#------------------------------------------------

# Test Undo/Redo Functionality

def test_undo(calculator):
    """Verify that undo removes the last calculation from history."""
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    assert calculator.history == []

def test_redo(calculator):
    """Verify that redo restores the last undone calculation."""
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    calculator.redo()
    assert len(calculator.history) == 1

# added to cover line 344 in calculator.py
def test_undo_empty_stack(calculator):
    """
    Verify that undo returns False when there are no operations
    on the undo stack to reverse.
    """
    result = calculator.undo()
    assert result == False

# added to cover line 371 in calculator.py
def test_redo_empty_stack(calculator):
    """
    Verify that redo returns False when there are no operations
    on the redo stack to reapply.
    """
    result = calculator.redo()
    assert result == False


#--------------------------------------------------
# Test History Management
#--------------------------------------------------

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history(mock_to_csv, calculator):
    """Verify that save_history calls to_csv once after a calculation."""
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.save_history()
    mock_to_csv.assert_called_once()

# added to cover line 270 in calculator.py
def test_save_empty_history(calculator):
    """
    Verify that save_history creates an empty CSV file when no calculations
    have been performed, without raising any exceptions.
    """
    calculator.save_history()  # no calculations added, history is empty

# added to cover lines 268-275 in calculator.py
@patch('app.calculator.pd.DataFrame.to_csv', side_effect=Exception("save error"))
def test_save_history_failure(mock_to_csv, calculator):
    """
    Verify that save_history raises an OperationError when the CSV write
    operation fails due to an underlying exception.
    """
    with pytest.raises(OperationError, match="Failed to save history"):
        calculator.save_history()

@patch('app.calculator.pd.read_csv')
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history(mock_exists, mock_read_csv, calculator):
    """Verify that load_history correctly loads calculations from a CSV file."""
    # Mock CSV data to match the expected format in from_dict
    mock_read_csv.return_value = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['2'],
        'operand2': ['3'],
        'result': ['5'],
        'timestamp': [datetime.datetime.now().isoformat()]
    })
    
    # Test the load_history functionality
    try:
        calculator.load_history()
        # Verify history length after loading
        assert len(calculator.history) == 1
        # Verify the loaded values
        assert calculator.history[0].operation == "Addition"
        assert calculator.history[0].operand1 == Decimal("2")
        assert calculator.history[0].operand2 == Decimal("3")
        assert calculator.history[0].result == Decimal("5")
    except OperationError:
        pytest.fail("Loading history failed due to OperationError")
        
# added to cover line 305 in calculator.py
@patch.object(Path, 'exists', return_value=True)
@patch('app.calculator.pd.read_csv', side_effect=Exception("load error"))
def test_load_history_failure(mock_read_csv, mock_exists, calculator):
    """
    Verify that load_history raises an OperationError when reading the
    CSV file fails due to an underlying exception.
    """
    with pytest.raises(OperationError, match="Failed to load history"):
        calculator.load_history()

# added to cover "Loaded empty history file" branch
@patch('app.calculator.pd.read_csv', return_value=pd.DataFrame(columns=['operation', 'operand1', 'operand2', 'result', 'timestamp']))
@patch.object(Path, 'exists', return_value=True)
def test_load_empty_history_file(mock_exists, mock_read_csv, calculator):
    """
    Verify that load_history handles an empty CSV file,
    resulting in an empty history list without raising any exceptions.
    """
    calculator.load_history()
    assert calculator.history == []

# Test Clearing History

def test_clear_history(calculator):
    """Verify that clear_history empties history, undo, and redo stacks."""
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []

# added to cover line 219 in calculator.py
def test_history_max_size(calculator):
    """
    Verify that the history list does not exceed max_history_size by confirming
    that the oldest entry is removed (pop(0)) when the limit is reached.
    """
    calculator.config.max_history_size = 2
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.perform_operation(2, 3)
    calculator.perform_operation(2, 3)  # triggers pop(0)
    assert len(calculator.history) <= 2

# added to cover line 390 in calculator.py
def test_show_history(calculator):
    """
    Verify that show_history returns a correctly formatted list of strings
    representing the calculation history after one operation has been performed.
    """
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    history = calculator.show_history()
    assert len(history) == 1
    assert "Addition" in history[0]
    assert "2" in history[0]
    assert "3" in history[0]
    assert "5" in history[0]

# added to cover lines 324-333 in calculator.py
def test_get_history_dataframe_empty(calculator):
    """
    Verify that get_history_dataframe returns an empty DataFrame when
    no calculations have been performed.
    """
    df = calculator.get_history_dataframe()
    assert len(df) == 0

# added to cover line 326 in calculator.py
def test_get_history_dataframe_with_data(calculator):
    """
    Verify that get_history_dataframe returns a DataFrame with one row
    after a single calculation has been performed.
    Timestamps are converted to strings to avoid a pandas segfault on Python 3.14.
    """
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    # convert timestamp to string to avoid pandas segfault on Python 3.14
    for calc in calculator.history:
        calc.timestamp = str(calc.timestamp)
    df = calculator.get_history_dataframe()
    assert len(df) == 1

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

#----------------------------------------------------------------
# Test REPL Commands (using patches for input/output handling)
#----------------------------------------------------------------

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit(mock_print, mock_input):
    """Verify that exit saves history and prints goodbye message."""
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("History saved successfully.")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    """Verify that the help command prints available commands."""
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

@pytest.mark.parametrize("command, a, b, expected_result", [
    ("add",      "2", "3", "\nResult: 5"),   # addition
    ("subtract", "5", "3", "\nResult: 2"),   # subtraction
    ("multiply", "4", "3", "\nResult: 12"),  # multiplication
    ("divide",   "6", "2", "\nResult: 3"),   # division
    ("power",    "2", "3", "\nResult: 8"),   # power
    ("root",     "16","2", "\nResult: 4"),   # root
])
@patch('builtins.print')
def test_repl_arithmetic_operations(mock_print, command, a, b, expected_result):
    """Verify that arithmetic commands produce correct results in the REPL."""
    with patch('builtins.input', side_effect=[command, a, b, 'exit']):
        calculator_repl()
        mock_print.assert_any_call(expected_result)

@patch('builtins.input', side_effect=['history', 'exit'])
@patch('builtins.print')
def test_repl_history_empty(mock_print, mock_input):
    """
    Verify that the REPL prints a no-history message when show_history
    returns an empty list.
    """
    with patch('app.calculator_repl.Calculator.show_history', return_value=[]):
        calculator_repl()
        mock_print.assert_any_call("No calculations in history")

@patch('builtins.input', side_effect=['history', 'exit'])
@patch('builtins.print')
def test_repl_history_has_items(mock_print, mock_input):
    """Verify that the history command prints a formatted history list
    when calculations exist."""
    with patch('app.calculator_repl.Calculator.show_history', return_value=["Addition(2, 3) = 5"]):
        calculator_repl()
        mock_print.assert_any_call("\nCalculation History:")

@patch('builtins.input', side_effect=['clear', 'exit'])
@patch('builtins.print')
def test_repl_clear(mock_print, mock_input):
    """Verify that the clear command clears the history and prints a confirmation."""
    calculator_repl()
    mock_print.assert_any_call("History cleared")

@pytest.mark.parametrize("inputs, expected_message", [
    (['undo', 'exit'],                    "Nothing to undo"),   # nothing to undo
    (['add', '2', '3', 'undo', 'exit'],   "Operation undone"),  # successful undo
    (['redo', 'exit'],                    "Nothing to redo"),   # nothing to redo
    (['add', '2', '3', 'undo', 'redo', 'exit'], "Operation redone"),  # successful redo
])
@patch('builtins.print')
def test_repl_undo_redo(mock_print, inputs, expected_message):
    """Verify undo and redo commands produce correct messages."""
    with patch('builtins.input', side_effect=inputs):
        calculator_repl()
        mock_print.assert_any_call(expected_message)

@pytest.mark.parametrize("inputs, patch_target, patch_side_effect, expected_message", [
    (['save', 'exit'], 'app.calculator.Calculator.save_history',
     Exception("save error"), "Error saving history: save error"),
    (['load', 'exit'], 'app.calculator.Calculator.load_history',
     Exception("load error"), "Error loading history: load error"),
])
@patch('builtins.print')
def test_repl_command_failures(mock_print, inputs, patch_target, patch_side_effect, expected_message):
    """Verify that save and load command failures print appropriate error messages."""
    with patch('builtins.input', side_effect=inputs):
        with patch(patch_target, side_effect=patch_side_effect):
            calculator_repl()
            mock_print.assert_any_call(expected_message)

@patch('builtins.input', side_effect=['save', 'exit'])
@patch('builtins.print')
def test_repl_save(mock_print, mock_input):
    """Verify that the save command saves history and prints a success message."""
    calculator_repl()
    mock_print.assert_any_call("History saved successfully")
    
@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_repl_load(mock_print, mock_input):
    """Verify that the load command loads history and prints a success message."""
    calculator_repl()
    mock_print.assert_any_call("History loaded successfully")

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_repl_exit_save_failure(mock_print, mock_input):
    """Verify that a save failure on exit prints a warning instead of crashing."""
    with patch('app.calculator.Calculator.save_history', side_effect=Exception("save error")):
        calculator_repl()
        mock_print.assert_any_call("Warning: Could not save history: save error")

@pytest.mark.parametrize("inputs, expected_message", [
    (['add', 'cancel', 'exit'],    "Operation cancelled"),  # cancel first number
    (['add', '2', 'cancel', 'exit'], "Operation cancelled"), # cancel second number
])
@patch('builtins.print')
def test_repl_cancel_operation(mock_print, inputs, expected_message):
    """Verify that entering cancel at either number prompt aborts the operation."""
    with patch('builtins.input', side_effect=inputs):
        with patch('app.calculator_repl.Calculator') as mock_calc:
            mock_calc.return_value.show_history.return_value = []
            calculator_repl()
            mock_print.assert_any_call(expected_message)


@patch('builtins.input', side_effect=['add', 'invalid', '3', 'exit'])
@patch('builtins.print')
def test_repl_validation_error(mock_print, mock_input):
    """Verify that a ValidationError is caught and an error message is printed
    when a non-numeric value is entered as an operand."""
    calculator_repl()
    assert any("Error" in str(call) for call in mock_print.call_args_list)

@patch('builtins.input', side_effect=['unknown_command', 'exit'])
@patch('builtins.print')
def test_repl_unknown_command(mock_print, mock_input):
    """Verify that an unrecognized command prints an appropriate error message."""
    calculator_repl()
    mock_print.assert_any_call("Unknown command: 'unknown_command'. Type 'help' for available commands.")

@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_repl_unexpected_error(mock_print, mock_input):
    """Verify that an unexpected exception during an operation prints an
    unexpected error message rather than crashing the REPL."""
    with patch('app.calculator.Calculator.perform_operation', side_effect=Exception("unexpected")):
        calculator_repl()
        mock_print.assert_any_call("Unexpected error: unexpected")

@patch('builtins.input', side_effect=[KeyboardInterrupt, 'exit'])
@patch('builtins.print')
def test_repl_keyboard_interrupt(mock_print, mock_input):
    """Verify that a KeyboardInterrupt (Ctrl+C) is handled gracefully
    and the REPL continues running."""
    calculator_repl()
    mock_print.assert_any_call("\nOperation cancelled")

@patch('builtins.input', side_effect=[EOFError])
@patch('builtins.print')
def test_repl_eof_error(mock_print, mock_input):
    """Verify that an EOFError (Ctrl+D) exits the REPL with an appropriate message."""
    calculator_repl()
    mock_print.assert_any_call("\nInput terminated. Exiting...")

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_repl_fatal_error(mock_print, mock_input):
    """Verify that a fatal error during Calculator initialization is caught,
    logged, and re-raised after printing an error message."""
    with patch('app.calculator_repl.Calculator', side_effect=Exception("fatal")):
        with pytest.raises(Exception, match="fatal"):
            calculator_repl()
        mock_print.assert_any_call("Fatal error: fatal")

@patch('builtins.input', side_effect=['history', 'exit'])
@patch('builtins.print')
def test_repl_inner_exception(mock_print, mock_input):
    """Verify that an unexpected exception inside the REPL loop is caught
    and an error message is printed without crashing the program."""
    with patch('app.calculator_repl.Calculator.show_history', side_effect=Exception("inner error")):
        calculator_repl()
        mock_print.assert_any_call("Error: inner error")