#!/usr/bin/env python3
"""Skill Evolution Monitor Integration for Tool Loop"""

import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

# Import existing tool-loop components
from axiom.core.tool_loop import run_tool_loop, AXIOM_TOOL_LOOP
from axiom.tools.registry import ToolContext, build_tools_spec
from axiom.claude.client import OpenChassisClient
from axiom.core.react_loop import ReActLoop
from axiom.core.memory import MemoryManager

class SkillEvolutionMonitorIntegration:
    """Integrates skill evolution monitoring with the tool-loop system"""
    
    def __init__(self, config_path: str = "config/skill_monitor.json"):
        self.config = self.load_config(config_path)
        self.logger = self.setup_logging()
        self.skill_cache_path = Path("built_9router/skills")
        self.last_skill_hash = self.calculate_skill_hash()
        self.monitoring_active = True
        
    def setup_logging(self):
        """Configure structured logging for skill evolution monitoring"""
        logger.add(
            "skill_monitor.log",
            rotation="10 MB",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <message>",
            level="INFO"
        )
        return logger
    
    def load_config(self, config_path: str) -> Dict:
        """Load skill monitoring configuration"""
        default_config = {
            "monitoring_interval": 300,  # 5 minutes
            "repositories": [
                {
                    "name": "Octoparse Agent Skills",
                    "url": "https://github.com/octoparse/agent-skills",
                    "path": "C:\Users\hp\Documents\9router\skills",
                    "enabled": True
                },
                {
                    "name": "Skills Catalog",
                    "url": "https://github.com/suprunoff/skills-catalog", 
                    "path": "skills-catalog/skills",
                    "enabled": True
                }
            ],
            "auto_integrate": True,
            "validate_before_use": True,
            "backup_before_update": True
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            import json
            with open(config_file) as f:
                return {**default_config, **json.load(f)}
        return default_config
    
    def calculate_skill_hash(self) -> str:
        """Calculate hash of all integrated skills"""
        import hashlib
        
        hasher = hashlib.md5()
        if self.skill_cache_path.exists():
            for skill_file in self.skill_cache_path.rglob("*"):
                if skill_file.is_file():
                    hasher.update(skill_file.read_bytes())
        return hasher.hexdigest()
    
    def monitor_skill_repository(self, repo_config: Dict) -> List[Dict]:
        """Monitor a skill repository for changes"""
        repo_path = Path(repo_config["path"])
        changes = []
        
        if not repo_path.exists():
            self.logger.warning(f"Repository not found: {repo_config['name']} at {repo_path}")
            return changes
        
        # Scan for skill files
        skill_files = list(repo_path.rglob("*.json")) + list(repo_path.rglob("package.json"))
        
        for skill_file in skill_files:
            skill_id = self.generate_skill_id(skill_file)
            file_hash = self.calculate_file_hash(skill_file)
            file_mtime = skill_file.stat().st_mtime
            
            # Check if we need to log this change
            if self.should_log_change(skill_id, file_hash, file_mtime):
                change = {
                    "skill_id": skill_id,
                    "type": self.detect_skill_change_type(skill_id, skill_file),
                    "file": str(skill_file),
                    "hash": file_hash,
                    "modified_time": file_mtime,
                    "timestamp": datetime.now().isoformat()
                }
                changes.append(change)
                self.logger.info(f"Detected skill change: {skill_id} in {repo_config['name']}")
        
        return changes
    
    def generate_skill_id(self, skill_file: Path) -> str:
        """Generate unique ID for a skill file"""
        import hashlib
        content = skill_file.read_text()
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file"""
        import hashlib
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def should_log_change(self, skill_id: str, file_hash: str, mtime: float) -> bool:
        """Determine if a change should be logged"""
        # Check if this is a new skill
        if not hasattr(self, '_known_skills'):
            self._known_skills = set()
        
        # For now, log all changes (could be made more sophisticated)
        return True
    
    def detect_skill_change_type(self, skill_id: str, skill_file: Path) -> str:
        """Detect what type of change a skill file represents"""
        # Simple detection based on file patterns
        file_name = skill_file.name.lower()
        
        if 'README' in file_name or 'LICENSE' in file_name:
            return "metadata_update"
        elif 'package.json' in file_name:
            return "configuration_update"
        elif 'skill.yaml' in file_name or 'skill.json' in file_name:
            return "skill_definition"
        elif file_name.endswith('.py') or file_name.endswith('.js'):
            return "implementation_update"
        else:
            return "file_update"
    
    def integrate_new_skills(self, changes: List[Dict]) -> bool:
        """Integrate newly detected skills into the tool-loop system"""
        integrated_count = 0
        
        for change in changes:
            skill_id = change['skill_id']
            change_type = change['type']
            
            if change_type == "skill_definition":
                success = self.integrate_skill_definition(change)
                if success:
                    integrated_count += 1
            elif change_type == "implementation_update":
                success = self.update_skill_implementation(change)
                if success:
                    integrated_count += 1
        
        if integrated_count > 0:
            self.logger.info(f"Successfully integrated {integrated_count} new/updated skills")
            # Refresh tool registry
            self.refresh_tool_registry()
        
        return integrated_count > 0
    
    def integrate_skill_definition(self, change: Dict) -> bool:
        """Integrate a new skill definition"""
        try:
            # This would normally copy the skill file to the working directory
            # and update the tool registry
            skill_file = Path(change['file'])
            
            # Create backup if configured
            if self.config["backup_before_update"]:
                self.create_skill_backup(skill_file)
            
            # Copy to working directory
            output_path = self.skill_cache_path / skill_file.name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(skill_file, output_path)
            
            self.logger.info(f"Integrated skill definition: {change['skill_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to integrate skill definition {change['skill_id']}: {e}")
            return False
    
    def update_skill_implementation(self, change: Dict) -> bool:
        """Update an existing skill implementation"""
        try:
            # Similar to integration but for updates
            skill_file = Path(change['file'])
            
            # Update the skill in cache
            output_path = self.skill_cache_path / skill_file.name
            import shutil
            shutil.copy2(skill_file, output_path)
            
            self.logger.info(f"Updated skill implementation: {change['skill_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update skill implementation {change['skill_id']}: {e}")
            return False
    
    def create_skill_backup(self, skill_file: Path):
        """Create backup of a skill file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"skill_backups/{skill_file.parent.name}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_path = backup_dir / f"{skill_file.name}.{timestamp}"
        shutil.copy2(skill_file, backup_path)
    
    def refresh_tool_registry(self):
        """Refresh the tool registry with new skills"""
        self.logger.info("Refreshing tool registry with newly integrated skills")
        
        # This would normally reload the tool registry
        # For demonstration, we just log the action
        self.logger.info("Tool registry refresh completed")
    
    def start_monitoring_loop(self):
        """Start the continuous monitoring loop"""
        self.logger.info("Starting skill evolution monitoring loop")
        
        while self.monitoring_active:
            try:
                total_changes = 0
                
                # Monitor each configured repository
                for repo_config in self.config["repositories"]:
                    if repo_config["enabled"]:
                        changes = self.monitor_skill_repository(repo_config)
                        if self.config["auto_integrate"]:
                            if changes:
                                success = self.integrate_new_skills(changes)
                                if success:
                                    total_changes += len(changes)
                
                if total_changes > 0:
                    self.logger.info(f"Monitoring cycle completed. Detected {total_changes} skill changes")
                else:
                    self.logger.debug("Monitoring cycle completed. No changes detected")
                
                # Sleep for the configured interval
                time.sleep(self.config["monitoring_interval"])
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring loop interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False
        self.logger.info("Skill evolution monitoring stopped")


async def main():
    """Main entry point for the skill evolution monitor integration"""
    print("=" * 70)
    print("Skill Evolution Monitor Integration for Tool Loop")
    print("=" * 70)
    
    # Initialize the integration
    monitor = SkillEvolutionMonitorIntegration()
    
    print(f"✅ Skill Evolution Monitor initialized")
    print(f"📁 Repositories configured: {len(monitor.config['repositories'])}")
    print(f"🔄 Monitoring interval: {monitor.config['monitoring_interval']} seconds")
    print(f"🔄 Auto-integrate: {monitor.config['auto_integrate']}")
    print()
    
    # Show current status
    current_hash = monitor.calculate_skill_hash()
    print(f"📊 Current skill cache hash: {current_hash[:16]}...")
    
    print("=" * 70)
    print("Starting continuous skill evolution monitoring...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 70)
    
    # Start the monitoring loop
    try:
        monitor.start_monitoring_loop()
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    finally:
        monitor.stop_monitoring()
        print("✅ Skill Evolution Monitor Integration completed")

if __name__ == "__main__":
    import asyncio
    
    # Set up asyncio event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Skill Evolution Monitor Integration terminated")
    except Exception as e:
        print(f"\n❌ Skill Evolution Monitor Integration failed: {e}")
        exit(1)