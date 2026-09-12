#!/usr/bin/env python3
"""
Test script to verify the architecture refactoring works correctly.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    try:
        from axiom.core.prompt_builder import PromptBuilder
        print("  ✅ PromptBuilder imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import PromptBuilder: {e}")
        return False
    
    try:
        from axiom.core.self_critique_engine import SelfCritiqueEngine, DecisionThresholds, CritiqueScores, SelfCritiqueResult
        print("  ✅ SelfCritiqueEngine and related classes imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import SelfCritiqueEngine: {e}")
        return False
    
    try:
        from axiom.core.react_loop import ReActLoop
        print("  ✅ ReActLoop imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import ReActLoop: {e}")
        return False
    
    return True


def test_prompt_builder():
    """Test PromptBuilder functionality."""
    print("\n🧪 Testing PromptBuilder...")
    try:
        from axiom.core.prompt_builder import PromptBuilder, AGENT_ICONS, AGENT_INSTRUCTIONS
        
        # Test instantiation
        builder = PromptBuilder()
        print("  ✅ PromptBuilder instantiated successfully")
        
        # Test constants
        assert "AGENT_ARCHITECT" in AGENT_ICONS
        assert "AGENT_CODER" in AGENT_INSTRUCTIONS
        print("  ✅ Constants (AGENT_ICONS, AGENT_INSTRUCTIONS) accessible")
        
        # Test that methods exist
        assert hasattr(builder, 'build_system_prompt')
        assert hasattr(builder, 'build_user_prompt')
        assert hasattr(builder, 'build_self_critique_prompt')
        print("  ✅ All required methods exist")
        
        return True
    except Exception as e:
        print(f"  ❌ PromptBuilder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_self_critique_engine():
    """Test SelfCritiqueEngine functionality."""
    print("\n🧪 Testing SelfCritiqueEngine...")
    try:
        from axiom.core.self_critique_engine import (
            SelfCritiqueEngine, 
            DecisionThresholds, 
            CritiqueScores, 
            SelfCritiqueResult
        )
        
        # Test instantiation
        engine = SelfCritiqueEngine(claude=None)
        print("  ✅ SelfCritiqueEngine instantiated successfully")
        
        # Test thresholds
        thresholds = DecisionThresholds()
        assert hasattr(thresholds, 'LIVRAISON_MIN')
        assert hasattr(thresholds, 'ITERATION_MIN')
        print("  ✅ DecisionThresholds has required attributes")
        
        # Test Pydantic models
        scores = CritiqueScores()
        assert scores.pertinence == 5.0
        print("  ✅ CritiqueScores model works")
        
        result = SelfCritiqueResult.get_default()
        assert "scores" in result
        assert "decision" in result
        print("  ✅ SelfCritiqueResult.get_default() works")
        
        # Test engine methods
        assert hasattr(engine, 'evaluate')
        assert hasattr(engine, '_parse_critique_response')
        assert hasattr(engine, '_determine_decision')
        assert hasattr(engine, '_fallback_quality_eval')
        print("  ✅ All required methods exist")
        
        return True
    except Exception as e:
        print(f"  ❌ SelfCritiqueEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_react_loop_integration():
    """Test that ReActLoop integrates with the new components."""
    print("\n🧪 Testing ReActLoop integration...")
    try:
        from axiom.core.react_loop import ReActLoop
        from axiom.core.prompt_builder import PromptBuilder
        from axiom.core.self_critique_engine import SelfCritiqueEngine
        
        # Check that ReActLoop has the new parameters
        import inspect
        sig = inspect.signature(ReActLoop.__init__)
        params = list(sig.parameters.keys())
        
        assert 'prompt_builder' in params, "prompt_builder parameter missing"
        assert 'self_critique_engine' in params, "self_critique_engine parameter missing"
        print("  ✅ ReActLoop has prompt_builder and self_critique_engine parameters")
        
        # Test that methods exist
        assert hasattr(ReActLoop, '_execute_iteration')
        assert hasattr(ReActLoop, '_self_critique')
        assert hasattr(ReActLoop, '_infer_task_type')
        print("  ✅ All required methods exist")
        
        # Check that old methods are removed
        assert not hasattr(ReActLoop, '_build_system_prompt'), "_build_system_prompt should be removed"
        assert not hasattr(ReActLoop, '_build_user_prompt'), "_build_user_prompt should be removed"
        assert not hasattr(ReActLoop, '_get_agent_instructions'), "_get_agent_instructions should be removed"
        print("  ✅ Old duplicate methods have been removed")
        
        return True
    except Exception as e:
        print(f"  ❌ ReActLoop integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_duplicate_code():
    """Verify that duplicate code has been removed."""
    print("\n🧪 Testing for no duplicate code...")
    try:
        # Read react_loop.py
        with open(os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core', 'react_loop.py'), 'r') as f:
            react_loop_content = f.read()
        
        # Check that old prompt building methods are not present
        assert '_build_system_prompt' not in react_loop_content or 'def _build_system_prompt' not in react_loop_content
        assert '_build_user_prompt' not in react_loop_content or 'def _build_user_prompt' not in react_loop_content
        assert '_get_agent_instructions' not in react_loop_content or 'def _get_agent_instructions' not in react_loop_content
        assert '_fallback_quality_eval' not in react_loop_content or 'def _fallback_quality_eval' not in react_loop_content
        print("  ✅ No duplicate methods found in react_loop.py")
        
        # Check that types are not duplicated
        assert 'class CritiqueScores' not in react_loop_content
        assert 'class SelfCritiqueResult' not in react_loop_content
        print("  ✅ No duplicate type definitions found")
        
        return True
    except Exception as e:
        print(f"  ❌ Duplicate code check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Test that all expected files exist."""
    print("\n🧪 Testing file structure...")
    base_path = os.path.join(os.path.dirname(__file__), 'backend', 'axiom', 'core')
    
    expected_files = [
        'react_loop.py',
        'prompt_builder.py',
        'self_critique_engine.py',
        'system_prompt.py',
    ]
    
    for filename in expected_files:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            print(f"  ✅ {filename} exists")
        else:
            print(f"  ❌ {filename} is missing")
            return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING APEX v4.0 ARCHITECTURE REFACTORING")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("PromptBuilder", test_prompt_builder),
        ("SelfCritiqueEngine", test_self_critique_engine),
        ("ReActLoop Integration", test_react_loop_integration),
        ("No Duplicate Code", test_no_duplicate_code),
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
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
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
