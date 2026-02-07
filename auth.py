import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

DB = "users.db"

def init_db():
    """Initialize the database with users table"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Create users table with additional fields
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT 1
        )
        """)
        
        # Create user_sessions table for tracking
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        conn.commit()
        print(f"✓ Database initialized successfully at {DB}")
        
    except sqlite3.Error as e:
        print(f"✗ Database initialization error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_user(email, password, role="user"):
    """
    Create a new user in the database
    
    Args:
        email: User email (must be unique)
        password: Plain text password
        role: User role (default: 'user')
    
    Returns:
        dict: User information or error
    """
    # Validate inputs
    if not email or not password:
        return {"success": False, "error": "Email and password are required"}
    
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}
    
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Check if user already exists
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = c.fetchone()
        
        if existing_user:
            return {"success": False, "error": "User with this email already exists"}
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Insert new user
        c.execute(
            """INSERT INTO users (email, password, role, created_at) 
               VALUES (?, ?, ?, ?)""",
            (email, hashed_password, role, datetime.now().isoformat())
        )
        
        user_id = c.lastrowid
        
        conn.commit()
        
        # Get the created user
        c.execute(
            "SELECT id, email, role, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user_data = c.fetchone()
        
        user_info = {
            "id": user_data[0],
            "email": user_data[1],
            "role": user_data[2],
            "created_at": user_data[3]
        }
        
        return {"success": True, "user": user_info}
        
    except sqlite3.Error as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
    finally:
        if conn:
            conn.close()

def validate_user(email, password):
    """
    Validate user credentials
    
    Args:
        email: User email
        password: Plain text password
    
    Returns:
        dict: User information if valid, None otherwise
    """
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Get user with active status
        c.execute(
            """SELECT id, email, password, role, is_active 
               FROM users WHERE email = ?""", 
            (email,)
        )
        row = c.fetchone()
        
        if not row:
            return None
        
        user_id, user_email, hashed_password, role, is_active = row
        
        # Check if user is active
        if not is_active:
            return None
        
        # Verify password
        if check_password_hash(hashed_password, password):
            # Update last login time
            c.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
            
            return {
                "id": user_id,
                "email": user_email,
                "role": role,
                "is_active": bool(is_active)
            }
        
        return None
        
    except sqlite3.Error as e:
        print(f"Database error during validation: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        c.execute(
            """SELECT id, email, role, created_at, last_login, is_active 
               FROM users WHERE id = ?""",
            (user_id,)
        )
        row = c.fetchone()
        
        if row:
            return {
                "id": row[0],
                "email": row[1],
                "role": row[2],
                "created_at": row[3],
                "last_login": row[4],
                "is_active": bool(row[5])
            }
        
        return None
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_user_password(email, new_password):
    """Update user password"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        hashed_password = generate_password_hash(new_password)
        
        c.execute(
            "UPDATE users SET password = ? WHERE email = ?",
            (hashed_password, email)
        )
        
        conn.commit()
        return c.rowcount > 0
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def list_users():
    """List all users (admin function)"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        c.execute(
            "SELECT id, email, role, created_at, last_login, is_active FROM users"
        )
        rows = c.fetchall()
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "email": row[1],
                "role": row[2],
                "created_at": row[3],
                "last_login": row[4],
                "is_active": bool(row[5])
            })
        
        return users
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_user(email):
    """Delete a user"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        c.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        
        return c.rowcount > 0
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Initialize database when module is imported
if not os.path.exists(DB):
    init_db()

# Test function
def test_auth():
    """Test the authentication system"""
    print("Testing authentication system...")
    
    # Initialize database
    init_db()
    
    # Test user creation
    test_email = "test@example.com"
    test_password = "password123"
    
    print(f"\n1. Creating user: {test_email}")
    result = create_user(test_email, test_password, "admin")
    if result["success"]:
        print(f"✓ User created successfully: {result['user']}")
    else:
        print(f"✗ User creation failed: {result.get('error', 'Unknown error')}")
    
    # Test duplicate user
    print(f"\n2. Testing duplicate user creation: {test_email}")
    result = create_user(test_email, "anotherpassword")
    if not result["success"]:
        print(f"✓ Correctly prevented duplicate user: {result.get('error')}")
    
    # Test validation
    print(f"\n3. Testing valid login for: {test_email}")
    user = validate_user(test_email, test_password)
    if user:
        print(f"✓ Login successful: {user}")
    else:
        print(f"✗ Login failed")
    
    # Test invalid password
    print(f"\n4. Testing invalid password for: {test_email}")
    user = validate_user(test_email, "wrongpassword")
    if not user:
        print("✓ Correctly rejected invalid password")
    
    # Test non-existent user
    print(f"\n5. Testing non-existent user")
    user = validate_user("nonexistent@example.com", "password")
    if not user:
        print("✓ Correctly rejected non-existent user")
    
    # List users
    print(f"\n6. Listing all users:")
    users = list_users()
    for u in users:
        print(f"  - {u['email']} ({u['role']})")

# Run tests if this file is executed directly
if __name__ == "__main__":
    test_auth()