# NEFUNGUJE
import sys
import os

# Add the parent directory to path to make source package importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from source.modules.database import SessionLocal
from source.models import User, RegistrationKey  # Import your models

def delete_item():
    # Create a database session
    db = SessionLocal()
    try:
        # Replace these parameters with your actual criteria
        #model_name = input("Enter model name (User, RegistrationKey, etc.): ")
        #field_name = input("Enter field name to filter by (id, email, key, etc.): ")
        #field_value = input("Enter value to match: ")
        
        model_name = "User"
        field_name = "email"
        field_value = "faltynekvojtech@gmail.com"

        # Select the model
        if model_name.lower() == "user":
            model = User
        elif model_name.lower() == "registrationkey":
            model = RegistrationKey
        else:
            print(f"Model {model_name} not found")
            return
        
        # Prepare the filter
        filter_expr = getattr(model, field_name) == field_value
        
        # Find the item
        item = db.query(model).filter(filter_expr).first()
        
        if not item:
            print(f"No {model_name} found with {field_name}={field_value}")
            return
            
        print(f"Found item: {item}")
        confirmation = input("Delete this item? (y/n): ")
        
        if confirmation.lower() == 'y':
            db.delete(item)
            db.commit()
            print("Item deleted successfully")
        else:
            print("Deletion cancelled")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_item()