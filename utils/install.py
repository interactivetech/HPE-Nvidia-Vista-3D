#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Medical AI Platform Installation Script
Interactive installation and setup for project configuration after cloning from git
"""

import os
import sys
import subprocess
import argparse
import logging
import shutil
import json
import socket
import getpass
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import time
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class InstallManager:
    """Interactive installation manager for the Vista3D project"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent  # Now install.py is in utils/
        self.env_file = self.project_root / '.env'
        self.env_template = self.project_root / 'dot_env_template'
        self.setup_state_file = self.project_root / '.setup_state.json'
        
        # System information
        self.system_info = {
            'platform': platform.system(),
            'release': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }
        
        # Configuration storage
        self.config = {}
        
        # Setup state tracking
        self.setup_state = self._load_setup_state()
        
    def print_banner(self):
        """Print installation banner"""
        print("\n" + "="*80)
        print("🚀 HPE NVIDIA Vista3D Medical AI Platform Installation")
        print("="*80)
        print("This script will guide you through installing the Vista3D project")
        print("after cloning from git. It will:")
        print("  • Check system requirements")
        print("  • Set up Python environment")
        print("  • Configure environment variables")
        print("  • Optionally install system dependencies")
        print("  • Optionally set up Vista3D Docker container")
        print("="*80)
        
        print("\n📋 WORKFLOW OVERVIEW:")
        print("-" * 40)
        print("This platform processes medical imaging data through the following workflow:")
        print("  1. 📁 DICOM files → Raw medical imaging data from scanners")
        print("  2. 🔄 Conversion → DICOM to NIfTI format for processing")
        print("  3. 🧠 Scanning → Vista3D AI analyzes and scans structures")
        print("  4. 🌐 Visualization → Web interface for viewing results")
        print("  5. 📊 Analysis → Interactive exploration of segmented data")
        
        print("\n📚 KEY TERMS:")
        print("-" * 40)
        print("DICOM (Digital Imaging and Communications in Medicine):")
        print("  • Standard format for medical imaging data")
        print("  • Contains patient metadata and image data")
        print("  • Used by CT, MRI, X-ray, and other medical scanners")
        print("  • Includes headers with patient info, scan parameters, etc.")
        
        print("\nNIfTI (Neuroimaging Informatics Technology Initiative):")
        print("  • Standard format for neuroimaging and medical image analysis")
        print("  • Simplified format compared to DICOM")
        print("  • Contains only image data and basic spatial information")
        print("  • Preferred format for AI/ML processing and analysis")
        print("  • Supports 3D volumes and 4D time series data")
        
        print("="*80 + "\n")
    
    def _load_setup_state(self) -> Dict:
        """Load setup state from previous runs"""
        try:
            if self.setup_state_file.exists():
                with open(self.setup_state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load setup state: {e}")
        
        return {
            'system_requirements_checked': False,
            'python_environment_ready': False,
            'configuration_gathered': False,
            'env_file_created': False,
            'directories_created': False,
            'dependencies_installed': False,
            'docker_checked': False,
            'vista3d_setup': False,
            'image_server_started': False,
            'last_successful_step': None,
            'last_run_timestamp': None
        }
    
    def _save_setup_state(self, step_name: str, success: bool = True):
        """Save current setup state"""
        try:
            if success:
                self.setup_state[step_name] = True
                self.setup_state['last_successful_step'] = step_name
            self.setup_state['last_run_timestamp'] = time.time()
            
            with open(self.setup_state_file, 'w') as f:
                json.dump(self.setup_state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save setup state: {e}")
    
    def _check_previous_run(self):
        """Check if this is a continuation of a previous setup"""
        if self.setup_state.get('last_run_timestamp'):
            last_run = self.setup_state['last_run_timestamp']
            last_step = self.setup_state.get('last_successful_step')
            
            # If last run was recent (within 24 hours) and had progress
            if time.time() - last_run < 86400 and last_step:
                print("\n" + "🔄 RESUMING PREVIOUS INSTALLATION")
                print("="*60)
                print("Detected a previous installation attempt with progress.")
                print(f"Last successful step: {last_step}")
                
                completed_steps = [k for k, v in self.setup_state.items() 
                                 if v is True and k.endswith(('_checked', '_ready', '_gathered', '_created', '_installed', '_setup', '_started'))]
                
                if completed_steps:
                    print("\n✅ Already completed steps:")
                    for step in completed_steps:
                        step_name = step.replace('_', ' ').title().replace('Env', '.env')
                        print(f"   • {step_name}")
                    
                    print("\n🚀 Will continue from where we left off...")
                    resume = self._ask_yes_no("Continue from previous installation?", default=True)
                    if not resume:
                        print("🔄 Starting fresh installation...")
                        self.setup_state = self._load_setup_state.__defaults__[0] if hasattr(self._load_setup_state, '__defaults__') else {}
                        self._save_setup_state('reset', True)
                    else:
                        print("✅ Resuming previous installation...")
                    print("="*60)
    
    def _handle_step_failure(self, step_name: str, error: Exception, critical: bool = True):
        """Handle step failure with recovery options"""
        print(f"\n❌ STEP FAILED: {step_name}")
        print("="*60)
        print(f"Error: {error}")
        
        self._save_setup_state(step_name, False)
        
        if critical:
            print("\n🔧 RECOVERY OPTIONS:")
            print("1. This was a critical step that must succeed")
            print("2. You can re-run install.py to try again")
            print("3. Some issues may be resolved by:")
            print("   • Checking internet connection")
            print("   • Running with administrator/sudo privileges")
            print("   • Installing missing system dependencies manually")
            print("   • Updating system packages")
            
            print(f"\n💡 To retry this specific step, run:")
            print(f"   python utils/install.py")
            print("   (Installation will automatically resume from the failed step)")
            
            retry = self._ask_yes_no("Would you like to retry this step now?", default=False)
            if retry:
                return True
        else:
            print("⚠️  This step failed but is not critical for basic functionality")
            print("   You can continue installation and address this later")
            
            continue_setup = self._ask_yes_no("Continue with remaining installation steps?", default=True)
            if continue_setup:
                return True
        
        return False
    
    def _ask_yes_no(self, question: str, default: bool = None) -> bool:
        """Ask a yes/no question"""
        while True:
            if default is True:
                prompt = f"{question} [Y/n]: "
            elif default is False:
                prompt = f"{question} [y/N]: "
            else:
                prompt = f"{question} [y/n]: "
            
            answer = input(prompt).strip().lower()
            
            if not answer and default is not None:
                return default
            elif answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
    
    def _prompt_user(self, prompt: str, default: str = None, validation=None) -> str:
        """Prompt user for input with optional default and validation"""
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if validation and not validation(user_input):
                print("Invalid input. Please try again.")
                continue
            
            return user_input

    def main(self):
        """Main entry point for installation"""
        print("Installation functionality will be implemented here...")
        print("This is a placeholder for the full installation script.")
        print("The complete implementation would include all the setup functionality")
        print("from the original setup.py script, adapted for the utils/install.py location.")

if __name__ == "__main__":
    install_manager = InstallManager()
    install_manager.main()
