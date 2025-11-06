#!/usr/bin/env python3
"""
EMERGENCY SCRIPT: Disable Maintenance Mode
This script manually disables maintenance mode by editing the maintenance.json file.
Run this if IT users are locked out and cannot access the system.
"""

import os
import json

# Path to maintenance.json file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAINTENANCE_FILE_PATH = os.path.join(BASE_DIR, 'instance', 'maintenance.json')

def disable_maintenance():
    """Manually disable maintenance mode"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(MAINTENANCE_FILE_PATH), exist_ok=True)
        
        # Read current state
        try:
            with open(MAINTENANCE_FILE_PATH, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {"enabled": False, "message": ""}
        
        # Disable maintenance mode
        state['enabled'] = False
        
        # Write back
        with open(MAINTENANCE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
        
        print("✅ SUCCESS: Maintenance mode has been DISABLED!")
        print(f"   File updated: {MAINTENANCE_FILE_PATH}")
        print(f"   Current state: {state}")
        print("\n📝 Next steps:")
        print("   1. Restart your Flask application server")
        print("   2. IT users should now be able to log in normally")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to disable maintenance mode: {e}")
        print(f"\n🔧 Manual fix:")
        print(f"   1. Open this file: {MAINTENANCE_FILE_PATH}")
        print(f"   2. Change 'enabled' to false:")
        print(f'      {{"enabled": false, "message": "..."}}')
        print(f"   3. Save the file")
        print(f"   4. Restart your Flask server")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("EMERGENCY: Disabling Maintenance Mode")
    print("=" * 60)
    disable_maintenance()

