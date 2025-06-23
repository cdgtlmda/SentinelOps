# Contributing to SentinelOps

Thank you for your interest in contributing to SentinelOps! This document provides guidelines and best practices for contributing to this ADK-based security operations platform.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [ADK Development Guidelines](#adk-development-guidelines)
- [Creating New ADK Tools](#creating-new-adk-tools)
- [Agent Development Best Practices](#agent-development-best-practices)
- [Testing ADK Components](#testing-adk-components)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/cdgtlmda/SentinelOps.git
   cd SentinelOps
   ```
3. Install ADK:
   ```bash
   pip install -e ./adk
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Environment

### Required Tools
- Python 3.9+
- Google Cloud SDK
- Docker (for local testing)
- Agent Development Kit (ADK)

### Environment Setup
1. Copy `.env.example` to `.env`
2. Configure GCP credentials
3. Set up local Firestore emulator (optional)

## ADK Development Guidelines

### Understanding ADK Architecture
All SentinelOps agents are built on Google's Agent Development Kit:
- Agents inherit from `SentinelOpsBaseAgent` (which extends `LlmAgent`)
- Business logic is encapsulated in tools inheriting from `BaseTool`
- Agent communication uses ADK transfer tools

### Key ADK Concepts
1. **Tools**: Encapsulate specific functionality
2. **Transfers**: Enable agent-to-agent communication
3. **Sessions**: Maintain conversation state
4. **Context**: Share information between agents

## Creating New ADK Tools

### Tool Template
```python
from typing import Dict, Any, List
from google.adk.tools import BaseTool, Field

class MyNewTool(BaseTool):
    """Brief description of what this tool does."""
    
    name: str = "my_new_tool"
    description: str = "Detailed description for the LLM to understand when to use this tool"
    
    # Define input parameters
    param1: str = Field(description="Description of param1")
    param2: int = Field(default=10, description="Description of param2")
    
    def execute(self) -> Dict[str, Any]:
        """Execute the tool's main functionality."""
        try:
            # Tool implementation
            result = self._perform_action()
            
            return {
                "success": True,
                "result": result,
                "message": "Action completed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Action failed"
            }
    
    def _perform_action(self):
        """Private method for tool logic."""
        # Implementation details
        pass
```

### Tool Best Practices
1. **Single Responsibility**: Each tool should do one thing well
2. **Clear Descriptions**: Help the LLM understand when to use the tool
3. **Error Handling**: Always catch and return meaningful errors
4. **Input Validation**: Validate parameters in the execute method
5. **Return Consistency**: Use consistent return format across tools

## Agent Development Best Practices

### Creating New Agents
1. Extend `SentinelOpsBaseAgent`:
   ```python
   from src.common.adk_agent_base import SentinelOpsBaseAgent
   
   class MyNewAgent(SentinelOpsBaseAgent):
       def __init__(self, **kwargs):
           super().__init__(
               name="my_new_agent",
               description="What this agent does",
               model="gemini-1.5-flash",
               tools=[MyTool1(), MyTool2()],
               **kwargs
           )
   ```

2. Register appropriate tools
3. Implement any agent-specific logic
4. Add transfer tools for communication

### Agent Guidelines
- **Stateless Design**: Agents should not maintain state between runs
- **Tool Composition**: Complex logic goes in tools, not agents
- **Error Recovery**: Implement robust error handling
- **Logging**: Use structured logging for debugging
- **Testing**: Write comprehensive tests for all agents

## Testing ADK Components

### Testing Tools
```python
import pytest
from unittest.mock import Mock, patch
from src.tools.my_tool import MyNewTool

class TestMyNewTool:
    def test_execute_success(self):
        tool = MyNewTool(param1="test", param2=20)
        
        with patch.object(tool, '_perform_action') as mock_action:
            mock_action.return_value = "test_result"
            
            result = tool.execute()
            
            assert result["success"] is True
            assert result["result"] == "test_result"
    
    def test_execute_error(self):
        tool = MyNewTool(param1="test")
        
        with patch.object(tool, '_perform_action') as mock_action:
            mock_action.side_effect = Exception("Test error")
            
            result = tool.execute()
            
            assert result["success"] is False
            assert "Test error" in result["error"]
```

### Testing Agents
```python
class TestMyNewAgent:
    @pytest.fixture
    def agent(self):
        return MyNewAgent()
    
    def test_agent_initialization(self, agent):
        assert agent.name == "my_new_agent"
        assert len(agent.tools) > 0
    
    def test_agent_tool_execution(self, agent):
        # Test agent's ability to execute tools
        pass
```

### Integration Testing
- Test agent-to-agent transfers
- Verify end-to-end workflows
- Use ADK test utilities
- Mock external services

## Pull Request Process

### Before Submitting
1. Ensure all tests pass: `pytest`
2. Run linting: `ruff check .`
3. Format code: `ruff format .`
4. Update documentation
5. Add tests for new functionality

### PR Guidelines
1. **Title**: Use clear, descriptive titles
   - ✅ "Add anomaly detection tool for login patterns"
   - ❌ "Fix stuff"

2. **Description**: Include:
   - What changes were made
   - Why they were necessary
   - How they were tested
   - Any breaking changes

3. **Size**: Keep PRs focused and small
   - One feature/fix per PR
   - Large changes should be discussed first

4. **Reviews**: Address all review comments

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
```

## Code Style

### Python Style
- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

### ADK-Specific Style
- Tool names: `snake_case`
- Tool classes: `PascalCase` ending with `Tool`
- Agent classes: `PascalCase` ending with `Agent`
- Transfer tools: Start with `TransferTo`

### Documentation
- Docstrings for all public methods
- Type hints for all parameters
- Examples in complex tool descriptions

## Commit Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### Examples
```
feat(detection): add DDoS detection tool

Implement new tool for detecting DDoS attacks based on
request patterns and traffic anomalies.

- Monitor request rates per IP
- Detect traffic spikes
- Integrate with CloudArmor

Closes #123
```

### Best Practices
- Use present tense ("add" not "added")
- Keep subject line under 50 characters
- Explain what and why, not how
- Reference issues when applicable

## Getting Help

- **Documentation**: Check `/docs` folder
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions
- **ADK Help**: Refer to ADK documentation

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

---

Thank you for contributing to SentinelOps! Your efforts help make cloud security more accessible and automated.