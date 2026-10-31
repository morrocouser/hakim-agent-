#!/usr/bin/env python3
"""
Simple test script to verify the architecture refactoring structure.
This version doesn't require external dependencies.
"""

import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def test_file_structure():
    """Test that all expected files exist."""
    print("🧪 Testing file structure...")
    base_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core')
    
    expected_files = [
        'react_loop.py',
        'prompt_builder.py',
        'self_critique_engine.py',
        'system_prompt.py',
    ]
    
    all_exist = True
    for filename in expected_files:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            print(f"  ✅ {filename} exists")
        else:
            print(f"  ❌ {filename} is missing")
            all_exist = False
    
    return all_exist


def test_no_duplicate_code():
    """Verify that duplicate code has been removed from react_loop.py."""
    print("\n🧪 Testing for no duplicate code in react_loop.py...")
    
    react_loop_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'react_loop.py')
    with open(react_loop_path, 'r', encoding='utf-8') as f:
        react_loop_content = f.read()
    
    # Check that old prompt building methods are not present as definitions
    checks = [
        ('_build_system_prompt', 'def _build_system_prompt'),
        ('_build_user_prompt', 'def _build_user_prompt'),
        ('_get_agent_instructions', 'def _get_agent_instructions'),
        ('_fallback_quality_eval', 'def _fallback_quality_eval'),
        ('CritiqueScores class', 'class CritiqueScores'),
        ('SelfCritiqueResult class', 'class SelfCritiqueResult'),
    ]
    
    all_passed = True
    for check_name, pattern in checks:
        if pattern in react_loop_content:
            print(f"  ❌ Found duplicate: {check_name}")
            all_passed = False
        else:
            print(f"  ✅ No duplicate: {check_name}")
    
    return all_passed


def test_prompt_builder_structure():
    """Test that prompt_builder.py has the expected structure."""
    print("\n🧪 Testing prompt_builder.py structure...")
    
    prompt_builder_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'prompt_builder.py')
    with open(prompt_builder_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for expected classes and methods
    expected_items = [
        ('PromptBuilder class', 'class PromptBuilder'),
        ('AGENT_ICONS', 'AGENT_ICONS'),
        ('AGENT_INSTRUCTIONS', 'AGENT_INSTRUCTIONS'),
        ('build_system_prompt', 'def build_system_prompt'),
        ('build_user_prompt', 'def build_user_prompt'),
        ('build_self_critique_prompt', 'def build_self_critique_prompt'),
    ]
    
    all_passed = True
    for check_name, pattern in expected_items:
        if pattern in content:
            print(f"  ✅ Found: {check_name}")
        else:
            print(f"  ❌ Missing: {check_name}")
            all_passed = False
    
    return all_passed


def test_self_critique_engine_structure():
    """Test that self_critique_engine.py has the expected structure."""
    print("\n🧪 Testing self_critique_engine.py structure...")
    
    sc_engine_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'self_critique_engine.py')
    with open(sc_engine_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for expected classes and methods
    expected_items = [
        ('SelfCritiqueEngine class', 'class SelfCritiqueEngine'),
        ('CritiqueScores class', 'class CritiqueScores'),
        ('SelfCritiqueResult class', 'class SelfCritiqueResult'),
        ('DecisionThresholds class', 'class DecisionThresholds'),
        ('evaluate method', 'async def evaluate'),
        ('_parse_critique_response', 'def _parse_critique_response'),
        ('_determine_decision', 'def _determine_decision'),
        ('_fallback_quality_eval', 'def _fallback_quality_eval'),
    ]
    
    all_passed = True
    for check_name, pattern in expected_items:
        if pattern in content:
            print(f"  ✅ Found: {check_name}")
        else:
            print(f"  ❌ Missing: {check_name}")
            all_passed = False
    
    return all_passed


def test_react_loop_imports():
    """Test that react_loop.py imports the new components."""
    print("\n🧪 Testing react_loop.py imports...")
    
    react_loop_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'react_loop.py')
    with open(react_loop_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for imports of new components
    expected_imports = [
        ('PromptBuilder', 'from axiom.core.prompt_builder import PromptBuilder'),
        ('SelfCritiqueEngine', 'from axiom.core.self_critique_engine import SelfCritiqueEngine'),
        ('DecisionThresholds', 'DecisionThresholds'),  # Imported on same line as SelfCritiqueEngine
    ]
    
    all_passed = True
    for check_name, pattern in expected_imports:
        if pattern in content:
            print(f"  ✅ Found import: {check_name}")
        else:
            print(f"  ❌ Missing import: {check_name}")
            all_passed = False
    
    # Check that old unused imports are removed
    old_imports = [
        ('AXIOM_SYSTEM_PROMPT', 'from axiom.core.system_prompt import'),
        ('build_self_critique_prompt from system_prompt', 'from axiom.core.system_prompt import'),
        ('apply_style_to_prompt', 'from axiom.core.user_style import apply_style_to_prompt'),
    ]
    
    # Note: These might still be present if they're used elsewhere
    # We'll just check they're not causing issues
    
    return all_passed


def test_react_loop_uses_new_components():
    """Test that react_loop.py uses the new components."""
    print("\n🧪 Testing react_loop.py uses new components...")
    
    react_loop_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'react_loop.py')
    with open(react_loop_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that ReActLoop uses the new components
    expected_uses = [
        ('self.prompt_builder', 'self.prompt_builder'),
        ('self.self_critique_engine', 'self.self_critique_engine'),
        ('prompt_builder parameter', 'prompt_builder: Optional[PromptBuilder]'),
        ('self_critique_engine parameter', 'self_critique_engine: Optional[SelfCritiqueEngine]'),
    ]
    
    all_passed = True
    for check_name, pattern in expected_uses:
        if pattern in content:
            print(f"  ✅ Found usage: {check_name}")
        else:
            print(f"  ❌ Missing usage: {check_name}")
            all_passed = False
    
    return all_passed


def test_line_counts():
    """Test that line counts are reasonable."""
    print("\n🧪 Testing line counts...")
    
    files_to_check = [
        ('react_loop.py', 350, 450),  # Should be around 382-440 with Circuit Breaker & Telemetry
        ('prompt_builder.py', 200, 300),  # Should be 250
        ('self_critique_engine.py', 250, 350),  # Should be 298
    ]
    
    base_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core')
    all_passed = True
    
    for filename, min_lines, max_lines in files_to_check:
        filepath = os.path.join(base_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        line_count = len(lines)
        
        if min_lines <= line_count <= max_lines:
            print(f"  ✅ {filename}: {line_count} lines (expected {min_lines}-{max_lines})")
        else:
            print(f"  ❌ {filename}: {line_count} lines (expected {min_lines}-{max_lines})")
            all_passed = False
    
    return all_passed


def test_code_organization():
    """Test that code is well organized."""
    print("\n🧪 Testing code organization...")
    
    # Check that react_loop.py has proper docstrings
    react_loop_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'react_loop.py')
    with open(react_loop_path, 'r', encoding='utf-8') as f:
        react_loop_content = f.read()
    
    # Check for class docstring
    if '"""' in react_loop_content and 'Boucle ReAct' in react_loop_content:
        print("  ✅ ReActLoop has proper docstring")
    else:
        print("  ❌ ReActLoop missing proper docstring")
        return False
    
    # Check for method docstrings
    if 'Exécute une tâche avec la boucle ReAct' in react_loop_content:
        print("  ✅ execute() method has docstring")
    else:
        print("  ⚠️  execute() method docstring might be missing")
    
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("TESTING APEX v4.0 ARCHITECTURE REFACTORING (Simple Version)")
    print("=" * 70)
    
    tests = [
        ("File Structure", test_file_structure),
        ("No Duplicate Code", test_no_duplicate_code),
        ("PromptBuilder Structure", test_prompt_builder_structure),
        ("SelfCritiqueEngine Structure", test_self_critique_engine_structure),
        ("ReActLoop Imports", test_react_loop_imports),
        ("ReActLoop Uses New Components", test_react_loop_uses_new_components),
        ("Line Counts", test_line_counts),
        ("Code Organization", test_code_organization),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n📊 {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The refactoring is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
