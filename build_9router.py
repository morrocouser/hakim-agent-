#!/usr/bin/env python3
"""9router build script to initialize connection with free LLMs."""

import os
import json
import shutil
from pathlib import Path

SKILLS_DIR = Path(r"C:\Users\hp\Documents\9router\skills")
BUILD_DIR = Path.cwd() / "built_9router"

# Skills that should be included by default
DEFAULT_SKILLS = [
    "9router-chat",
    "9router-embeddings", 
    "9router-tts",
    "9router-web-search",
    "9router-web-fetch",
]

def check_skill_dependencies(skill_path):
    """Check if a skill has its dependencies installed."""
    package_json = skill_path / "package.json"
    if not package_json.exists():
        return True  # No dependencies to check
    
    with open(package_json) as f:
        pkg = json.load(f)
    
    # Check for dependencies
    deps = pkg.get("dependencies", {})
    missing_deps = []
    
    for dep, version in deps.items():
        if dep in ["python", "node", "go"]:
            continue  # System dependencies
            
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(f"{dep}>={version}")
    
    return len(missing_deps) == 0, missing_deps

def build_skill(skill_path, output_dir):
    """Build a single skill."""
    skill_name = skill_path.name
    print(f"\n🔨 Building skill: {skill_name}")
    
    # Check dependencies
    has_deps, missing = check_skill_dependencies(skill_path)
    if not has_deps:
        print(f"  ⚠️  Missing dependencies: {missing}")
        print(f"  ⚠️  Skipping {skill_name} (requires manual setup)")
        return False
    
    # Check for skill configuration
    config_files = ["package.json", "skill.yaml", "skill.json", "config.json"]
    config_file = None
    for cf in config_files:
        if (skill_path / cf).exists():
            config_file = skill_path / cf
            break
    
    if config_file:
        with open(config_file) as f:
            config = json.load(f)
        name = config.get("name", skill_name)
        version = config.get("version", "1.0.0")
        description = config.get("description", "No description")
        
        print(f"  📦 Skill Name: {name}")
        print(f"  🔢 Version: {version}")
        print(f"  📝 Description: {description[:80]}...")
    
    # Create skill output directory
    skill_output = output_dir / skill_name
    skill_output.mkdir(parents=True, exist_ok=True)
    
    # Copy skill files
    for item in skill_path.iterdir():
        if item.name in config_files or item.name in [".git", ".gitignore"]:
            continue
        if item.is_dir():
            shutil.copytree(item, skill_output / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, skill_output / item.name)
    
    print(f"  ✅ Successfully built skill: {skill_name}")
    return True

def build_all_skills():
    """Build all 9router skills."""
    print("=" * 60)
    print("🚀 Building 9router skills with free LLMs")
    print("=" * 60)
    
    if not SKILLS_DIR.exists():
        print(f"❌ Skills directory not found: {SKILLS_DIR}")
        return False
    
    skills = list(SKILLS_DIR.iterdir())
    print(f"📚 Found {len(skills)} skills in {SKILLS_DIR}")
    
    # Create output directory
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build skills
    built_count = 0
    skipped_count = 0
    
    for skill_path in skills:
        if not skill_path.is_dir():
            continue
            
        skill_name = skill_path.name
        
        # Check if skill should be built by default
        if skill_name in DEFAULT_SKILLS:
            success = build_skill(skill_path, BUILD_DIR)
            if success:
                built_count += 1
            else:
                skipped_count += 1
        else:
            # Confirm with user for optional skills
            print(f"\n📋 Skill {skill_name} is optional.")
            print(f"   Do you want to build it? (y/N): ", end="")
            response = input().strip().lower()
            
            if response in ["y", "yes", ""]:
                success = build_skill(skill_path, BUILD_DIR)
                if success:
                    built_count += 1
                else:
                    skipped_count += 1
    
    # Create build summary
    summary = {
        "timestamp": "2026-08-03",
        "source_directory": str(SKILLS_DIR),
        "total_skills": len(skills),
        "built_skills": built_count,
        "skipped_skills": skipped_count,
        "skills_directory": str(BUILD_DIR),
    }
    
    with open(BUILD_DIR / "build_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 60)
    print("📊 Build Summary:")
    print(f"  Built Skills: {built_count}")
    print(f"  Skipped Skills: {skipped_count}")
    print(f"  Output Directory: {BUILD_DIR}")
    print("=" * 60)
    
    return built_count > 0

def main():
    """Main entry point."""
    try:
        success = build_all_skills()
        if success:
            print("\n✅ Build completed successfully!")
            print("📁 Use the built skills from the 'built_9router' directory")
            return 0
        else:
            print("\n⚠️  Build completed with warnings")
            return 1
    except KeyboardInterrupt:
        print("\n❌ Build interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())