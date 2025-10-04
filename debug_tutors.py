
import os
import sys
from pprint import pprint

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import get_tutors_collection

def main():
    print("\n=== Tutor Database Debug ===\n")
    
    # Get the tutors collection
    tutors = get_tutors_collection()
    
    # Count all tutors
    total = tutors.count_documents({})
    print(f"Total tutors in database: {total}\n")
    
    if total == 0:
        print("No tutors found in the database.")
        return
    
    # Get all tutors
    all_tutors = list(tutors.find({}))
    
    # Print summary of each tutor
    for i, tutor in enumerate(all_tutors, 1):
        print(f"\n--- Tutor {i}/{total} ---")
        print(f"ID: {tutor.get('_id')}")
        print(f"Name: {tutor.get('name', 'N/A')}")
        print(f"Email: {tutor.get('email', 'N/A')}")
        
        # Print all fields that might be Telegram IDs
        id_fields = [f for f in tutor if any(id_key in f.lower() for id_key in ['telegram', 'userid', 'chatid', 'user_id', 'chat_id'])]
        if id_fields:
            print("Possible ID fields:")
            for field in id_fields:
                print(f"  {field}: {tutor[field]}")
        else:
            print("No Telegram ID fields found.")
            
        # Print all fields for debugging
        print("\nAll fields:")
        pprint({k: v for k, v in tutor.items() if k != '_id'})

if __name__ == "__main__":
    main()
