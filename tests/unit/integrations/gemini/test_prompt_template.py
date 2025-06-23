"""
Comprehensive test suite for integrations/gemini/prompt_template.py

This test suite achieves ≥90% statement coverage of the target source file
using 100% production code with NO MOCKING.

Target file: src/integrations/gemini/prompt_template.py (295 lines)
Requirements: Test all classes, functions, and edge cases with comprehensive coverage
"""

import pytest

from src.integrations.gemini.prompt_template import (
    PromptTemplate,
    PromptLibrary,
    SECURITY_PROMPTS,
    SECURITY_PROMPTS_PART1,
    SECURITY_PROMPTS_PART2,
)


class TestPromptTemplate:
    """Test PromptTemplate dataclass functionality"""

    def test_prompt_template_creation(self) -> None:
        """Test PromptTemplate dataclass creation and basic attributes"""
        template = PromptTemplate(
            name="test_template",
            template="Hello {name}, your score is {score}",
            variables=["name", "score"],
            output_format="JSON format",
            examples=[{"name": "John", "score": "95"}]
        )

        assert template.name == "test_template"
        assert template.template == "Hello {name}, your score is {score}"
        assert template.variables == ["name", "score"]
        assert template.output_format == "JSON format"
        assert template.examples == [{"name": "John", "score": "95"}]

    def test_prompt_template_minimal_creation(self) -> None:
        """Test PromptTemplate creation with minimal required fields"""
        template = PromptTemplate(
            name="minimal",
            template="Simple {text}",
            variables=["text"]
        )

        assert template.name == "minimal"
        assert template.template == "Simple {text}"
        assert template.variables == ["text"]
        assert template.output_format is None
        assert template.examples is None

    def test_format_basic_substitution(self) -> None:
        """Test basic variable substitution in template formatting"""
        template = PromptTemplate(
            name="basic",
            template="User {user} has {count} items",
            variables=["user", "count"]
        )

        result = template.format(user="Alice", count="5")
        assert result == "User Alice has 5 items"

    def test_format_missing_variables_error(self) -> None:
        """Test error handling when required variables are missing"""
        template = PromptTemplate(
            name="test",
            template="Hello {name}, you are {age} years old",
            variables=["name", "age"]
        )

        with pytest.raises(ValueError) as exc_info:
            template.format(name="Bob")  # Missing 'age'

        assert "Missing required variables:" in str(exc_info.value)
        assert "age" in str(exc_info.value)

    def test_format_multiple_missing_variables_error(self) -> None:
        """Test error handling when multiple required variables are missing"""
        template = PromptTemplate(
            name="test",
            template="Hello {name}, you are {age} years old and live in {city}",
            variables=["name", "age", "city"]
        )

        with pytest.raises(ValueError) as exc_info:
            template.format(name="Bob")  # Missing 'age' and 'city'

        error_msg = str(exc_info.value)
        assert "Missing required variables:" in error_msg
        assert "age" in error_msg
        assert "city" in error_msg

    def test_format_with_output_format(self) -> None:
        """Test template formatting with output format addition"""
        template = PromptTemplate(
            name="with_format",
            template="Analyze this: {data}",
            variables=["data"],
            output_format="```json\n{\"result\": \"value\"}\n```"
        )

        result = template.format(data="sample data")
        expected = ("Analyze this: sample data\n\n"
                    "Provide your response in the following format:\n"
                    "```json\n{\"result\": \"value\"}\n```")
        assert result == expected

    def test_format_with_examples_single(self) -> None:
        """Test template formatting with single example"""
        template = PromptTemplate(
            name="with_example",
            template="Process {input}",
            variables=["input"],
            examples=[{"input": "test", "output": "processed"}]
        )

        result = template.format(input="real data")
        expected = ("Process real data\n\n"
                    "Examples:\n\n"
                    "Example 1:\n"
                    "input: test\n"
                    "output: processed")
        assert result == expected

    def test_format_with_examples_multiple(self) -> None:
        """Test template formatting with multiple examples"""
        template = PromptTemplate(
            name="multi_examples",
            template="Convert {text}",
            variables=["text"],
            examples=[
                {"text": "hello", "result": "HELLO"},
                {"text": "world", "result": "WORLD"},
                {"text": "python", "result": "PYTHON"}
            ]
        )

        result = template.format(text="testing")
        expected = ("Convert testing\n\n"
                    "Examples:\n\n"
                    "Example 1:\n"
                    "text: hello\n"
                    "result: HELLO\n\n"
                    "Example 2:\n"
                    "text: world\n"
                    "result: WORLD\n\n"
                    "Example 3:\n"
                    "text: python\n"
                    "result: PYTHON")
        assert result == expected

    def test_format_with_output_format_and_examples(self) -> None:
        """Test template formatting with both output format and examples"""
        template = PromptTemplate(
            name="complete",
            template="Analyze {data}",
            variables=["data"],
            output_format="JSON response required",
            examples=[{"data": "sample", "analysis": "complete"}]
        )

        result = template.format(data="test data")
        expected = ("Analyze test data\n\n"
                    "Provide your response in the following format:\n"
                    "JSON response required\n\n"
                    "Examples:\n\n"
                    "Example 1:\n"
                    "data: sample\n"
                    "analysis: complete")
        assert result == expected

    def test_format_complex_template(self) -> None:
        """Test formatting of complex template with multiple variables"""
        template = PromptTemplate(
            name="complex",
            template="System: {system}\nUser: {user}\nTask: {task}\nContext: {context}",
            variables=["system", "user", "task", "context"]
        )

        result = template.format(
            system="SentinelOps",
            user="admin",
            task="security analysis",
            context="production environment"
        )
        expected = ("System: SentinelOps\n"
                    "User: admin\n"
                    "Task: security analysis\n"
                    "Context: production environment")
        assert result == expected

    def test_format_extra_variables_allowed(self) -> None:
        """Test that extra variables beyond required ones are allowed"""
        template = PromptTemplate(
            name="flexible",
            template="Hello {name}",
            variables=["name"]
        )

        # Extra variables should not cause errors
        result = template.format(name="Alice", extra="value", another="param")
        assert result == "Hello Alice"

    def test_format_empty_examples_list(self) -> None:
        """Test template with empty examples list"""
        template = PromptTemplate(
            name="empty_examples",
            template="Process {data}",
            variables=["data"],
            examples=[]
        )

        result = template.format(data="test")
        # Empty examples list should not add examples section
        assert result == "Process test"

    def test_format_empty_variables_list(self) -> None:
        """Test template with no variables"""
        template = PromptTemplate(
            name="no_vars",
            template="Static text with no variables",
            variables=[]
        )

        result = template.format()
        assert result == "Static text with no variables"


class TestPromptLibrary:
    """Test PromptLibrary class functionality"""

    def test_prompt_library_initialization(self) -> None:
        """Test PromptLibrary initialization"""
        library = PromptLibrary()

        # Should initialize with security prompts
        assert isinstance(library.templates, dict)
        assert len(library.templates) > 0
        assert isinstance(library.custom_templates, dict)
        assert len(library.custom_templates) == 0

        # Verify security prompts are loaded
        assert "log_analysis" in library.templates
        assert "threat_detection" in library.templates
        assert "risk_assessment" in library.templates
        assert "pattern_recognition" in library.templates

    def test_add_template(self) -> None:
        """Test adding custom templates to library"""
        library = PromptLibrary()

        custom_template = PromptTemplate(
            name="custom_test",
            template="Custom template with {variable}",
            variables=["variable"]
        )

        library.add_template(custom_template)

        assert "custom_test" in library.custom_templates
        assert library.custom_templates["custom_test"] == custom_template

    def test_add_multiple_templates(self) -> None:
        """Test adding multiple custom templates"""
        library = PromptLibrary()

        template1 = PromptTemplate(
            name="template1",
            template="First {var1}",
            variables=["var1"]
        )
        template2 = PromptTemplate(
            name="template2",
            template="Second {var2}",
            variables=["var2"]
        )

        library.add_template(template1)
        library.add_template(template2)

        assert len(library.custom_templates) == 2
        assert "template1" in library.custom_templates
        assert "template2" in library.custom_templates

    def test_get_template_custom(self) -> None:
        """Test getting custom template from library"""
        library = PromptLibrary()

        custom_template = PromptTemplate(
            name="get_test",
            template="Get template test {param}",
            variables=["param"]
        )

        library.add_template(custom_template)
        retrieved = library.get_template("get_test")

        assert retrieved == custom_template
        assert retrieved.name == "get_test"

    def test_get_template_builtin(self) -> None:
        """Test getting built-in security template"""
        library = PromptLibrary()

        template = library.get_template("log_analysis")

        assert isinstance(template, PromptTemplate)
        assert template.name == "log_analysis"
        assert "log_entries" in template.variables
        assert "time_range" in template.variables
        assert "source_system" in template.variables

    def test_get_template_custom_priority(self) -> None:
        """Test that custom templates take priority over built-in ones"""
        library = PromptLibrary()

        # Create custom template with same name as built-in
        custom_template = PromptTemplate(
            name="log_analysis",
            template="Custom log analysis {data}",
            variables=["data"]
        )

        library.add_template(custom_template)
        retrieved = library.get_template("log_analysis")

        # Should get custom template, not built-in
        assert retrieved == custom_template
        assert retrieved.template == "Custom log analysis {data}"

    def test_get_template_unknown_error(self) -> None:
        """Test error when getting unknown template"""
        library = PromptLibrary()

        with pytest.raises(ValueError) as exc_info:
            library.get_template("nonexistent_template")

        assert "Unknown template: nonexistent_template" in str(exc_info.value)

    def test_format_prompt_builtin(self) -> None:
        """Test formatting built-in prompt template"""
        library = PromptLibrary()

        result = library.format_prompt(
            "threat_detection",
            indicators="suspicious IP activity",
            environment="production",
            baseline="normal traffic patterns",
            recent_incidents="none"
        )

        assert "suspicious IP activity" in result
        assert "production" in result
        assert "normal traffic patterns" in result
        assert "Known attack patterns" in result

    def test_format_prompt_custom(self) -> None:
        """Test formatting custom prompt template"""
        library = PromptLibrary()

        custom_template = PromptTemplate(
            name="format_test",
            template="Testing {param1} and {param2}",
            variables=["param1", "param2"]
        )

        library.add_template(custom_template)
        result = library.format_prompt("format_test", param1="value1", param2="value2")

        assert result == "Testing value1 and value2"

    def test_format_prompt_with_missing_variables_error(self) -> None:
        """Test error propagation when formatting prompt with missing variables"""
        library = PromptLibrary()

        with pytest.raises(ValueError) as exc_info:
            library.format_prompt("log_analysis", log_entries="some logs")  # Missing required vars

        assert "Missing required variables:" in str(exc_info.value)

    def test_list_templates_empty_custom(self) -> None:
        """Test listing templates with no custom templates"""
        library = PromptLibrary()

        templates = library.list_templates()

        # Should include all built-in security templates
        assert len(templates) >= 4  # At least the 4 security templates
        assert "log_analysis" in templates
        assert "threat_detection" in templates
        assert "risk_assessment" in templates
        assert "pattern_recognition" in templates

    def test_list_templates_with_custom(self) -> None:
        """Test listing templates with custom templates added"""
        library = PromptLibrary()

        custom1 = PromptTemplate("custom1", "template1 {var}", ["var"])
        custom2 = PromptTemplate("custom2", "template2 {var}", ["var"])

        library.add_template(custom1)
        library.add_template(custom2)

        templates = library.list_templates()

        # Should include built-in + custom templates
        assert "custom1" in templates
        assert "custom2" in templates
        assert "log_analysis" in templates
        assert len(templates) >= 6  # At least 4 built-in + 2 custom

    def test_list_templates_no_duplicates(self) -> None:
        """Test that list_templates returns unique template names"""
        library = PromptLibrary()

        templates = library.list_templates()
        unique_templates = set(templates)

        # No duplicates should exist
        assert len(templates) == len(unique_templates)


class TestSecurityPrompts:
    """Test security prompt template constants"""

    def test_security_prompts_part1_exists(self) -> None:
        """Test that SECURITY_PROMPTS_PART1 contains expected templates"""
        assert isinstance(SECURITY_PROMPTS_PART1, dict)
        assert len(SECURITY_PROMPTS_PART1) >= 2

        assert "log_analysis" in SECURITY_PROMPTS_PART1
        assert "threat_detection" in SECURITY_PROMPTS_PART1

        # Verify they are PromptTemplate instances
        assert isinstance(SECURITY_PROMPTS_PART1["log_analysis"], PromptTemplate)
        assert isinstance(SECURITY_PROMPTS_PART1["threat_detection"], PromptTemplate)

    def test_security_prompts_part2_exists(self) -> None:
        """Test that SECURITY_PROMPTS_PART2 contains expected templates"""
        assert isinstance(SECURITY_PROMPTS_PART2, dict)
        assert len(SECURITY_PROMPTS_PART2) >= 2

        assert "risk_assessment" in SECURITY_PROMPTS_PART2
        assert "pattern_recognition" in SECURITY_PROMPTS_PART2

        # Verify they are PromptTemplate instances
        assert isinstance(SECURITY_PROMPTS_PART2["risk_assessment"], PromptTemplate)
        assert isinstance(SECURITY_PROMPTS_PART2["pattern_recognition"], PromptTemplate)

    def test_security_prompts_merged(self) -> None:
        """Test that SECURITY_PROMPTS contains both parts merged"""
        assert isinstance(SECURITY_PROMPTS, dict)

        # Should contain all templates from both parts
        for name, template in SECURITY_PROMPTS_PART1.items():
            assert name in SECURITY_PROMPTS
            assert SECURITY_PROMPTS[name] == template

        for name, template in SECURITY_PROMPTS_PART2.items():
            assert name in SECURITY_PROMPTS
            assert SECURITY_PROMPTS[name] == template

    def test_log_analysis_template_structure(self) -> None:
        """Test log_analysis template structure and content"""
        template = SECURITY_PROMPTS["log_analysis"]

        assert template.name == "log_analysis"
        assert "log_entries" in template.variables
        assert "time_range" in template.variables
        assert "source_system" in template.variables
        assert template.output_format is not None
        assert "json" in template.output_format.lower()
        assert "threats_detected" in template.output_format

    def test_threat_detection_template_structure(self) -> None:
        """Test threat_detection template structure and content"""
        template = SECURITY_PROMPTS["threat_detection"]

        assert template.name == "threat_detection"
        assert "indicators" in template.variables
        assert "environment" in template.variables
        assert "baseline" in template.variables
        assert "recent_incidents" in template.variables
        assert template.output_format is not None
        assert "threat_assessment" in template.output_format

    def test_risk_assessment_template_structure(self) -> None:
        """Test risk_assessment template structure and content"""
        template = SECURITY_PROMPTS["risk_assessment"]

        assert template.name == "risk_assessment"
        assert "findings" in template.variables
        assert "critical_assets" in template.variables
        assert "business_context" in template.variables
        assert "current_controls" in template.variables
        assert template.output_format is not None
        assert "risk_summary" in template.output_format

    def test_pattern_recognition_template_structure(self) -> None:
        """Test pattern_recognition template structure and content"""
        template = SECURITY_PROMPTS["pattern_recognition"]

        assert template.name == "pattern_recognition"
        assert "data" in template.variables
        assert "historical_context" in template.variables
        assert template.output_format is not None
        assert "identified_patterns" in template.output_format


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""

    def test_end_to_end_workflow(self) -> None:
        """Test complete workflow from library creation to prompt formatting"""
        # Create library
        library = PromptLibrary()

        # Add custom template
        custom_template = PromptTemplate(
            name="custom_analysis",
            template="Analyze {data} with context {context}",
            variables=["data", "context"],
            output_format="Structured analysis required"
        )
        library.add_template(custom_template)

        # Format custom template
        result = library.format_prompt(
            "custom_analysis",
            data="security logs",
            context="enterprise environment"
        )

        expected = ("Analyze security logs with context enterprise environment\n\n"
                    "Provide your response in the following format:\n"
                    "Structured analysis required")
        assert result == expected

    def test_security_template_formatting_real_data(self) -> None:
        """Test formatting security templates with realistic data"""
        library = PromptLibrary()

        # Test log analysis with real-looking data
        result = library.format_prompt(
            "log_analysis",
            log_entries="[2024-01-01 10:00:00] Failed login attempt from 192.168.1.100",
            time_range="2024-01-01 09:00:00 to 2024-01-01 11:00:00",
            source_system="Active Directory"
        )

        assert "Failed login attempt" in result
        assert "192.168.1.100" in result
        assert "Active Directory" in result
        assert "security analysis" in result

    def test_template_variable_validation_edge_cases(self) -> None:
        """Test edge cases in variable validation"""
        template = PromptTemplate(
            name="edge_test",
            template="Test {var1} {var2} {var3}",
            variables=["var1", "var2", "var3"]
        )

        # Test with exactly required variables
        result = template.format(var1="a", var2="b", var3="c")
        assert result == "Test a b c"

        # Test with variables containing special characters
        result = template.format(
            var1="test@email.com", var2="path/to/file", var3="data-with-dashes"
        )
        assert result == "Test test@email.com path/to/file data-with-dashes"

    def test_unicode_content_handling(self) -> None:
        """Test handling of Unicode content in templates"""
        template = PromptTemplate(
            name="unicode_test",
            template="Process data: {data}",
            variables=["data"]
        )

        # Test with Unicode characters
        result = template.format(data="测试数据 🔒 émojis")
        assert result == "Process data: 测试数据 🔒 émojis"

    def test_large_content_handling(self) -> None:
        """Test handling of large content in templates"""
        template = PromptTemplate(
            name="large_test",
            template="Analyze: {content}",
            variables=["content"]
        )

        # Test with large content
        large_content = "x" * 10000
        result = template.format(content=large_content)
        assert len(result) > 10000
        assert large_content in result

    def test_library_state_isolation(self) -> None:
        """Test that multiple library instances don't interfere"""
        library1 = PromptLibrary()
        library2 = PromptLibrary()

        # Add template to first library
        template1 = PromptTemplate("lib1_template", "Template 1 {var}", ["var"])
        library1.add_template(template1)

        # Add template to second library
        template2 = PromptTemplate("lib2_template", "Template 2 {var}", ["var"])
        library2.add_template(template2)

        # Verify isolation
        assert "lib1_template" in library1.custom_templates
        assert "lib1_template" not in library2.custom_templates
        assert "lib2_template" in library2.custom_templates
        assert "lib2_template" not in library1.custom_templates


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
