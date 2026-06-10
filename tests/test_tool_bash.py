import pytest

from tools.bash import BASH_TOOL_DEFINITION, BashToolInput, execute_bash_tool


class TestBashToolDefinition:
    def test_has_correct_name(self):
        assert BASH_TOOL_DEFINITION.name == "bash"

    def test_has_required_fields(self):
        assert "command" in BASH_TOOL_DEFINITION.input_schema["required"]


@pytest.mark.asyncio
class TestExecuteBashTool:
    async def test_simple_command(self):
        result = await execute_bash_tool(BashToolInput(command="echo hello"))
        assert result == "hello"

    async def test_multi_line_output(self):
        result = await execute_bash_tool(
            BashToolInput(command="echo 'line1'; echo 'line2'")
        )
        assert "line1" in result
        assert "line2" in result

    async def test_capture_stderr(self):
        result = await execute_bash_tool(
            BashToolInput(command="echo error >&2")
        )
        assert "STDERR:" in result
        assert "error" in result

    async def test_non_zero_exit_code(self):
        with pytest.raises(ValueError, match="Exit code 42"):
            await execute_bash_tool(BashToolInput(command="exit 42"))

    async def test_command_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            await execute_bash_tool(BashToolInput(command="nonexistent_cmd_xyz"))

    async def test_timeout(self):
        with pytest.raises(ValueError, match="[Tt]ime"):
            await execute_bash_tool(BashToolInput(command="sleep 60", timeout=0.5))

    async def test_no_output(self):
        result = await execute_bash_tool(BashToolInput(command="true"))
        assert result == "(no output)"

    async def test_pipe_command(self):
        result = await execute_bash_tool(
            BashToolInput(command="echo 'hello world' | tr 'a-z' 'A-Z'")
        )
        assert result == "HELLO WORLD"