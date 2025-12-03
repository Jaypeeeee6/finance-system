"""
Script to initialize location priorities in the database.
This will create LocationPriority entries for existing locations with default priorities.

Run this script once after adding the LocationPriority model to migrate existing locations.
"""

from app import app
from models import db, LocationPriority, Branch
from datetime import datetime

def init_location_priorities():
    """Initialize location priorities with default values"""
    with app.app_context():
        # Default priorities (matching the old hardcoded order)
        default_priorities = {
            'Office': 1,
            'Kucu': 2,
            'Boom': 3,
            'Thoum': 4,
            'Kitchen': 5
        }
        
        # Get all unique locations from branches
        all_locations = db.session.query(Branch.restaurant).distinct().all()
        location_names = [loc[0] for loc in all_locations]
        
        print("Initializing location priorities...")
        print(f"Found {len(location_names)} unique locations: {', '.join(location_names)}")
        
        created_count = 0
        skipped_count = 0
        
        for location_name in location_names:
            # Check if location priority already exists
            existing = LocationPriority.query.filter_by(location_name=location_name).first()
            
            if existing:
                print(f"  ⚠ Skipping '{location_name}' - already exists with priority {existing.priority}")
                skipped_count += 1
                continue
            
            # Get priority from defaults, or use a high number for new locations
            priority = default_priorities.get(location_name, 999)
            
            try:
                location_priority = LocationPriority(
                    location_name=location_name,
                    priority=priority,
                    is_active=True,
                    created_by_user_id=None  # System initialization
                )
                
                db.session.add(location_priority)
                created_count += 1
                print(f"  ✓ Created '{location_name}' with priority {priority}")
                
            except Exception as e:
                print(f"  ✗ Error creating '{location_name}': {str(e)}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✓ Successfully created {created_count} location priorities")
            if skipped_count > 0:
                print(f"  (Skipped {skipped_count} existing entries)")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error committing changes: {str(e)}")
            return False
        
        # Display final status
        all_priorities = LocationPriority.query.order_by(LocationPriority.priority, LocationPriority.location_name).all()
        print(f"\nCurrent location priorities (ordered by priority):")
        for lp in all_priorities:
            status = "Active" if lp.is_active else "Inactive"
            print(f"  {lp.priority}. {lp.location_name} ({status})")
        
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("Location Priorities Initialization Script")
    print("=" * 60)
    print()
    
    success = init_location_priorities()
    
    print()
    print("=" * 60)
    if success:
        print("Initialization completed successfully!")
    else:
        print("Initialization completed with errors. Please review the output above.")
    print("=" * 60)

