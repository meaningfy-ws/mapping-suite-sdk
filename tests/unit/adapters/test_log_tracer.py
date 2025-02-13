import time

from mssdk.adapters.log_tracer import Tracer


def test_tracer_console_output(capsys):
    """
    Test Tracer with and without console output.
    """
    # Function with console output
    @Tracer.trace("test_with_console", print_on_console=True)
    def function_with_console():
        return "console output"

    # Function without console output
    @Tracer.trace("test_without_console", print_on_console=False)
    def function_without_console():
        return "no console output"

    # Execute functions
    result1 = function_with_console()
    result2 = function_without_console()

    # Check function results
    assert result1 == "console output"
    assert result2 == "no console output"

    # Get console output
    captured = capsys.readouterr()
    console_output = captured.out
    # Verify console output
    assert "test_with_console" in console_output  # Should be in output
    assert "test_without_console" not in console_output  # Should not be in output
    assert "function_with_console" in console_output  # Function name should be in attributes
    assert "success" in console_output  # Status should be in output