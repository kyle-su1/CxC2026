
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.session import Session # Import to register with SQLAlchemy
from app.services.preference_service import get_user_explicit_preferences, merge_weights

def test_user_isolation():
    db = SessionLocal()
    try:
        # 1. Setup Test Users
        print("--- Setting up Test Users ---")
        user_a = db.query(User).filter(User.email == "test_user_a@example.com").first()
        if not user_a:
            user_a = User(email="test_user_a@example.com", auth0_id="auth0|test_a", preferences={})
            db.add(user_a)
        
        user_b = db.query(User).filter(User.email == "test_user_b@example.com").first()
        if not user_b:
            user_b = User(email="test_user_b@example.com", auth0_id="auth0|test_b", preferences={})
            db.add(user_b)
        
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)
        
        print(f"User A ID: {user_a.id}")
        print(f"User B ID: {user_b.id}")
        
        # 2. Set Different Preferences
        print("\n--- Setting Preferences ---")
        # User A likes 'price' (Cheap)
        user_a.preferences = {"price_sensitivity": 0.9, "quality": 0.2}
        
        # User B likes 'quality' (Premium)
        user_b.preferences = {"price_sensitivity": 0.1, "quality": 0.9}
        
        db.commit()
        
        # 3. Verify Retrieval via Service
        print("\n--- Verifying Retrieval ---")
        prefs_a = get_user_explicit_preferences(db, user_a.id)
        prefs_b = get_user_explicit_preferences(db, user_b.id)
        
        print(f"User A Prefs (Expected High Price Sens): {prefs_a}")
        print(f"User B Prefs (Expected High Quality):    {prefs_b}")
        
        assert prefs_a['price_sensitivity'] > 0.8, "User A should be price sensitive"
        assert prefs_b['quality'] > 0.8, "User B should care about quality"
        assert prefs_a['price_sensitivity'] != prefs_b['price_sensitivity'], "Preferences must be different"
        
        print("\n✅ SUCCESS: User preferences are isolated correctly.")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup (Optional, but good for repeatability)
        # db.delete(user_a)
        # db.delete(user_b)
        # db.commit()
        db.close()

if __name__ == "__main__":
    test_user_isolation()
