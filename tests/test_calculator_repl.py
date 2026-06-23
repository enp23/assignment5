import pytest
from unittest.mock import patch
from app.calculator_repl import calculator_repl
from app.exceptions import OperationError

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