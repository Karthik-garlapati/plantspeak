import streamlit as st
from PIL import Image
import os
from datetime import datetime
import pandas as pd
import csv
import uuid
import base64
import requests
import json
import sqlite3
import hashlib
import re
import traceback
from functools import wraps

# Create directories for uploaded files if they don't exist
os.makedirs("uploads/photos", exist_ok=True)
os.makedirs("uploads/voice", exist_ok=True)
os.makedirs("uploads/notes", exist_ok=True)

# Database setup
def init_db():
    """Initialize the SQLite database with tables for users and submissions"""
    # Use timeout to wait for lock to be released (5 seconds)
    conn = sqlite3.connect('plantspeak.db', timeout=5.0)
    c = conn.cursor()
    
    try:
        # Begin transaction
        conn.execute('BEGIN IMMEDIATE')
        
        # Create users table
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            email TEXT UNIQUE,
            role TEXT,
            community TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create submissions table
        c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            submission_time TIMESTAMP,
            plant_name TEXT NOT NULL,
            entry_title TEXT,
            local_names TEXT,
            scientific_name TEXT,
            category TEXT,
            usage_desc TEXT,
            prep_method TEXT,
            community TEXT,
            tags TEXT,
            location TEXT,
            language TEXT,
            latitude REAL,
            longitude REAL,
            photo_path TEXT,
            voice_path TEXT,
            notes_path TEXT,
            age_group TEXT,
            submitter_role TEXT,
            submitter_name TEXT,
            contact_info TEXT,
            consent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        conn.commit()
    except sqlite3.OperationalError as e:
        # Handle locked database
        print(f"Database initialization error: {e}")
        conn.rollback()
    except Exception as e:
        # Handle other errors
        print(f"Unexpected error during db initialization: {e}")
        conn.rollback()
    finally:
        conn.close()

# Password handling
def hash_password(password):
    """Convert password to secure hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify the provided password against stored hash"""
    return stored_password == hash_password(provided_password)

# User management
def add_user(username, password, name='', email='', role='', community=''):
    """Add a new user to the database"""
    # Use timeout to wait for lock to be released (5 seconds)
    conn = sqlite3.connect('plantspeak.db', timeout=5.0)
    c = conn.cursor()
    hashed_pw = hash_password(password)
    success = False
    
    try:
        # Enable immediate transactions to reduce lock time
        conn.execute('BEGIN IMMEDIATE')
        c.execute(
            "INSERT INTO users (username, password, name, email, role, community) VALUES (?, ?, ?, ?, ?, ?)",
            (username, hashed_pw, name, email, role, community)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Handle duplicate username/email
        conn.rollback()
        success = False
    except sqlite3.OperationalError as e:
        # Handle locked database
        conn.rollback()
        print(f"Database error: {e}")
        success = False
    except Exception as e:
        # Handle any other errors
        conn.rollback()
        print(f"Unexpected error: {e}")
        success = False
    finally:
        conn.close()
    
    return success

def authenticate_user(username, password):
    """Check if username and password match a user in database"""
    conn = sqlite3.connect('plantspeak.db')
    c = conn.cursor()
    
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return verify_password(result[0], password)
    return False

def get_user_info(username):
    """Get user details from database"""
    conn = sqlite3.connect('plantspeak.db')
    c = conn.cursor()
    
    c.execute("SELECT id, username, name, email, role, community FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "username": result[1],
            "name": result[2],
            "email": result[3],
            "role": result[4],
            "community": result[5]
        }
    return None

# User session management
def check_login_status():
    """Check if a user is logged in"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_info = None
    
    return st.session_state.logged_in

def login_user(username):
    """Set session state for logged in user"""
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.user_info = get_user_info(username)

def logout_user():
    """Clear session state for logout"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_info = None

def update_user_profile(user_id, name=None, email=None, role=None, community=None, password=None):
    """Update user profile information in the database"""
    conn = sqlite3.connect('plantspeak.db')
    c = conn.cursor()
    
    update_fields = []
    params = []
    
    # Build the update query based on which fields are provided
    if name is not None:
        update_fields.append("name = ?")
        params.append(name)
    if email is not None:
        update_fields.append("email = ?")
        params.append(email)
    if role is not None:
        update_fields.append("role = ?")
        params.append(role)
    if community is not None:
        update_fields.append("community = ?")
        params.append(community)
    if password is not None:
        update_fields.append("password = ?")
        params.append(hash_password(password))
    
    # If there are fields to update
    if update_fields:
        # Add user_id to the params
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            c.execute(query, params)
            conn.commit()
            success = True
        except sqlite3.IntegrityError as e:
            # Most likely due to duplicate email
            print(f"Database update error: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    conn.close()
    return False  # No fields to update

# Submission database functions
def save_submission_to_db(
    submission_id, user_id, submission_time, plant_name, entry_title, local_names, scientific_name,
    category, usage_desc, prep_method, community, tags, location, language, lat, lon,
    photo_path, voice_path, notes_path, age_group="", submitter_role="", submitter_name="", contact_info="", consent=""
):
    """Save a plant submission to the database"""
    # Use timeout to wait for lock to be released (5 seconds)
    conn = sqlite3.connect('plantspeak.db', timeout=5.0)
    c = conn.cursor()
    success = False
    
    try:
        # Enable immediate transactions to reduce lock time
        conn.execute('BEGIN IMMEDIATE')
        c.execute('''
            INSERT INTO submissions (
                id, user_id, submission_time, plant_name, entry_title, local_names, scientific_name,
                category, usage_desc, prep_method, community, tags, location, language,
                latitude, longitude, photo_path, voice_path, notes_path, age_group, submitter_role,
                submitter_name, contact_info, consent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_id, user_id, submission_time, plant_name, entry_title, local_names, scientific_name,
            category, usage_desc, prep_method, community, tags, location, language, lat, lon,
            photo_path, voice_path, notes_path, age_group, submitter_role, submitter_name, contact_info, consent
        ))
        
        conn.commit()
        success = True
    except sqlite3.OperationalError as e:
        # Handle locked database
        conn.rollback()
        print(f"Database locked error: {e}")
        success = False
    except Exception as e:
        # Handle other errors
        conn.rollback()
        print(f"Database error: {e}")
        success = False
    finally:
        conn.close()
    
    return success

def get_user_submissions(user_id=None):
    """
    Get all submissions, optionally filtered by user_id.
    If user_id is provided, show all submissions by that user and public submissions by others.
    If user_id is None, only show public submissions (those with consent != 'No, keep private')
    """
    conn = sqlite3.connect('plantspeak.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    
    if user_id:
        # For logged-in users, show:
        # 1. All of their own submissions
        # 2. Public submissions from others
        c.execute('''
            SELECT s.*, u.username, u.name as submitter_name
            FROM submissions s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.user_id = ? OR (s.consent != 'No, keep private' AND s.consent IS NOT NULL)
            ORDER BY s.submission_time DESC
        ''', (user_id,))
    else:
        # For anonymous users or when not filtering by user, show only public submissions
        c.execute('''
            SELECT s.*, u.username, u.name as submitter_name
            FROM submissions s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.consent != 'No, keep private' AND s.consent IS NOT NULL
            ORDER BY s.submission_time DESC
        ''')
        
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return results

# Initialize the database
init_db()

# Function to get location name from coordinates using OpenStreetMap's Nominatim API
def get_location_from_coords(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "PlantSpeakApp/1.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "display_name" in data:
                return data["display_name"]
        return None
    except Exception as e:
        st.error(f"Error getting location: {e}")
        return None

# Function to get coordinates from a location name
def get_coords_from_location(location_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json"
        headers = {"User-Agent": "PlantSpeakApp/1.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except Exception as e:
        st.error(f"Error geocoding location: {e}")
        return None, None

st.set_page_config(page_title="🌿 PlantSpeak – Preserve Plant Knowledge", layout="wide")

# Check login status
is_logged_in = check_login_status()

# Initialize page selection in session state if not present
if 'page' not in st.session_state:
    st.session_state.page = 'login' if not is_logged_in else 'main'

# Sidebar navigation when logged in
if is_logged_in:
    st.sidebar.title(f"👤 Welcome, {st.session_state.username}!")
    
    # Navigation options
    st.sidebar.subheader("Navigation")
    page = st.sidebar.radio("Go to:", 
        ["📝 Add Entry", "📚 View Submissions", "👤 My Profile"]
    )
    
    # Map selection to session state
    if page == "📝 Add Entry":
        st.session_state.page = 'main'
    elif page == "📚 View Submissions":
        st.session_state.page = 'submissions'
    elif page == "👤 My Profile":
        st.session_state.page = 'profile'
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        logout_user()
        st.session_state.page = 'login'
        st.experimental_rerun()

# Login/Register Interface when not logged in
if not is_logged_in:
    # Choose between login and registration
    login_tab, register_tab = st.tabs(["🔑 Login", "📝 Register"])
    
    with login_tab:
        st.header("🔑 Login to PlantSpeak")
        
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            login_button = st.button("🔓 Login")
        
        if login_button:
            if authenticate_user(login_username, login_password):
                login_user(login_username)
                st.session_state.page = 'main'
                st.success(f"Welcome back, {login_username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    
    with register_tab:
        st.header("📝 Create an Account")
        
        reg_username = st.text_input("Username (required)", key="reg_username")
        reg_password = st.text_input("Password (required)", type="password", key="reg_password")
        reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
        
        reg_name = st.text_input("Full Name (optional)", key="reg_name")
        reg_email = st.text_input("Email (optional)", key="reg_email")
        reg_role = st.text_input("Role (e.g., Farmer, Healer, Researcher)", key="reg_role")
        reg_community = st.text_input("Community or Organization", key="reg_community")
        
        register_button = st.button("✅ Register")
        
        if register_button:
            # Basic validation
            if not reg_username or not reg_password:
                st.error("Username and password are required")
            elif reg_password != reg_password_confirm:
                st.error("Passwords do not match")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters long")
            elif reg_email and not re.match(r"[^@]+@[^@]+\.[^@]+", reg_email):
                st.error("Please enter a valid email address")
            else:
                if add_user(reg_username, reg_password, reg_name, reg_email, reg_role, reg_community):
                    st.success("Registration successful! You can now log in.")
                    # Auto-login after registration
                    login_user(reg_username)
                    st.session_state.page = 'main'
                    st.experimental_rerun()
                else:
                    st.error("Username or email already exists")

# Main app only shown when logged in
if is_logged_in:
    # Declare tab variables at a higher scope so they can be checked before use
    tab1 = None
    tab2 = None
    
    if st.session_state.page == 'main' or st.session_state.page == 'submissions':
        # Create tabs for data entry and viewing data based on page selection
        tab1, tab2 = st.tabs(["📝 Add New Entry", "📚 View Submissions"])
        
        # Set which tab is active based on page selection
        if st.session_state.page == 'submissions':
            # This makes the second tab active
            tab2.active = True
    
    elif st.session_state.page == 'profile':
        # User profile page
        st.title("👤 My Profile")
        
        user_info = st.session_state.user_info
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Account Information")
            st.write(f"**Username:** {user_info['username']}")
            st.write(f"**Name:** {user_info['name'] or 'Not provided'}")
            st.write(f"**Email:** {user_info['email'] or 'Not provided'}")
            st.write(f"**Role:** {user_info['role'] or 'Not specified'}")
            st.write(f"**Community:** {user_info['community'] or 'Not specified'}")
        
        with col2:
            st.subheader("Statistics")
            
            # Get user submissions from database
            user_submissions = get_user_submissions(user_info['id'])
            st.write(f"**Your contributions:** {len(user_submissions)}")
        
        # Profile update form
        st.subheader("Update Profile")
        
        with st.form("profile_update_form"):
            update_name = st.text_input("Full Name", value=user_info['name'] or "")
            update_email = st.text_input("Email", value=user_info['email'] or "")
            update_role = st.text_input("Role (e.g., Farmer, Healer, Researcher)", value=user_info['role'] or "")
            update_community = st.text_input("Community or Organization", value=user_info['community'] or "")
            
            # Password change section
            st.subheader("Change Password (Optional)")
            update_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit_button = st.form_submit_button("Update Profile")
            
        if submit_button:
            # Validate input
            if update_email and not re.match(r"[^@]+@[^@]+\.[^@]+", update_email):
                st.error("Please enter a valid email address")
            elif update_password and len(update_password) < 6:
                st.error("Password must be at least 6 characters long")
            elif update_password and update_password != confirm_password:
                st.error("Passwords do not match")
            else:
                # Only update password if a new one was provided
                password_to_update = update_password if update_password else None
                
                # Update profile in database
                if update_user_profile(
                    user_info['id'], 
                    name=update_name, 
                    email=update_email, 
                    role=update_role, 
                    community=update_community,
                    password=password_to_update
                ):
                    st.success("Profile updated successfully!")
                    
                    # Update the session state with new information
                    user_info['name'] = update_name
                    user_info['email'] = update_email
                    user_info['role'] = update_role
                    user_info['community'] = update_community
                    st.session_state.user_info = user_info
                    
                    # Refresh the page to show the updated information
                    st.experimental_rerun()
                else:
                    st.error("Failed to update profile. The email may already be in use.")
        
## Only proceed with content tabs if we're on a page that has them and tabs are created
if not is_logged_in:
    # Not logged in: show nothing (login/register UI is already shown above)
    pass
elif tab1 is not None and st.session_state.page not in ['profile']:
    # Tab 1 - Add New Entry
    with tab1:
        st.title("🌿 PlantSpeak – Help Us Preserve Traditional Plant Knowledge")

        st.markdown("""
        Many elders, farmers, and healers hold deep knowledge about local plants — used in remedies, rituals, and daily life. This app helps collect, preserve, and share that knowledge.
        """)
        st.header("📥 Step 1: Upload or Identify the Plant")
        photo = st.file_uploader("📸 Upload a photo of the plant (leaf, flower, bark, etc.)", type=["jpg", "jpeg", "png"])
        plant_name = st.text_input("✍️ Enter the Name of the Plant (in any language)")
        entry_title = st.text_input("📝 Entry Title (Optional)", help="A title for your submission")

        st.header("🧾 Step 2: Share What You Know")
        local_names = st.text_area("1️⃣ Local Name(s) of the Plant", help="List local names in various languages or dialects")
        scientific_name = st.text_input("2️⃣ Scientific / Botanical Name (Optional)")

        category = st.multiselect("3️⃣ Category of Use", [
            "Medicinal", "Food / Cooking", "Religious / Ritual",
            "Ecological / Environmental", "Craft / Utility", "Other"
        ])

        usage_desc = st.text_area("4️⃣ Describe the Use of the Plant", help="E.g., Used to treat fever, offered in rituals, made into tea")
        prep_method = st.text_area("5️⃣ Explain the Preparation or Application Process", help="How is it prepared, how much is used, and how often?")
        community = st.text_input("6️⃣ Who Uses This Plant in Your Area?", help="Mention tribe, village, or community")
        tags = st.text_input("🔖 Tags or Keywords (Optional)", help="Separate by commas, e.g. headache, fever, forest plant")

        st.header("🌍 Step 3: Location & Language")
        location = st.text_input("7️⃣ Where is this Plant Found or Used?", help="Village, District, State")
        language = st.text_input("8️⃣ Language or Dialect You're Using")

        st.write("📍 **Geographic Location**")
        
        # Options for location entry
        loc_tab1, loc_tab2, loc_tab3 = st.tabs(["� Enter Name", "📱 Auto-Detect", "🔍 Enter Coordinates"])
        
        # Container for location controls and map
        location_container = st.container()
        
        # Define session state to track changes in lat/lon
        if 'prev_lat' not in st.session_state:
            st.session_state.prev_lat = 0.0
        if 'prev_lon' not in st.session_state:
            st.session_state.prev_lon = 0.0
        
        # Tab 1: Search location by name
        with loc_tab1:
            search_loc = st.text_input("🔍 Search for a location", help="Enter a place name, landmark, or address")
            if search_loc:
                if st.button("🔎 Find Location"):
                    with st.spinner("Searching location..."):
                        found_lat, found_lon = get_coords_from_location(search_loc)
                        if found_lat and found_lon:
                            st.session_state.temp_lat = found_lat
                            st.session_state.temp_lon = found_lon
                            st.success(f"Found coordinates: {found_lat}, {found_lon}")
                            st.experimental_rerun()
                        else:
                            st.error(f"Could not find location: {search_loc}")
        
        # Tab 2: Auto-detect location
        with loc_tab2:
            # Auto-location functionality
            st.info("This feature uses IP-based geolocation and may not be precise. Results may vary based on network setup.")
            
            if st.button("📱 Get My Location (Approx)"):
                # Use a free IP-based geolocation service
                try:
                    with st.spinner("Getting your approximate location..."):
                        ip_location_url = "https://ipapi.co/json/"
                        st.write("Making request to geolocation service...")
                        
                        response = requests.get(ip_location_url, timeout=10)
                        st.write(f"Received response with status code: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.write("Data received from geolocation service:", data)
                            
                            if "latitude" in data and "longitude" in data:
                                # Update session state to trigger rerun with new values
                                lat_value = data["latitude"]
                                lon_value = data["longitude"]
                                st.session_state.temp_lat = lat_value
                                st.session_state.temp_lon = lon_value
                                st.success(f"Located at approximately: {lat_value}, {lon_value}")
                                
                                # Display direct map to confirm location before rerun
                                st.map(data=pd.DataFrame({'lat': [lat_value], 'lon': [lon_value]}), zoom=10)
                                
                                if st.button("✅ Use This Location"):
                                    st.experimental_rerun()
                            else:
                                st.error("Location coordinates not found in API response")
                        else:
                            st.error(f"API request failed with status code: {response.status_code}")
                except Exception as e:
                    st.error(f"Could not detect location: {str(e)}")
                    import traceback
                    st.error(f"Error details: {traceback.format_exc()}")
        
            st.write("Or use an online service:")
            st.markdown("[🔍 Find My Coordinates](https://www.latlong.net/) (copy & paste back here)")
        
        # Tab 3: Manual coordinate entry
        with loc_tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                lat = st.number_input("📌 Latitude", format="%.6f")
            
            with col2:
                lon = st.number_input("📌 Longitude", format="%.6f")
        
        # Display map with the coordinates
        if lat != 0 and lon != 0:
            st.map(data=pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=12)
            
            # Check if coordinates have changed significantly (at least 0.0001 degrees difference)
            coords_changed = (abs(lat - st.session_state.prev_lat) > 0.0001 or 
                             abs(lon - st.session_state.prev_lon) > 0.0001)
            
            # Auto-fill location name if valid coordinates and they've changed
            if coords_changed:
                st.session_state.prev_lat = lat
                st.session_state.prev_lon = lon
                
                # Add a button to get location name from coordinates
                if st.button("📍 Get Location Name from Coordinates") or (location == "" and coords_changed):
                    with st.spinner("Getting location name..."):
                        place_name = get_location_from_coords(lat, lon)
                        if place_name:
                            # Store in session state to update on next rerun
                            st.session_state.location_name = place_name
                            st.success(f"Location detected: {place_name}")
                            if location == "":
                                st.experimental_rerun()
        
        # Apply detected location name if available
        if hasattr(st.session_state, 'location_name') and location == "":
            location = st.session_state.location_name
            del st.session_state.location_name

        # Check if we have temp coordinates to apply from auto-detection or search
        if hasattr(st.session_state, 'temp_lat') and hasattr(st.session_state, 'temp_lon'):
            lat = st.session_state.temp_lat
            lon = st.session_state.temp_lon
            # Clear the temporary values
            del st.session_state.temp_lat
            del st.session_state.temp_lon

        # Step 4: Voice & Text Extras
        st.header("🎤 Step 4: Voice & Text Extras")
        voice_note = st.file_uploader("9️⃣ Upload a Voice Recording", type=["mp3", "wav", "m4a"])
        notes_scan = st.file_uploader("🔠 10️⃣ Upload Handwritten or Printed Notes", type=["jpg", "jpeg", "png", "pdf"])

        # Step 5: About You
        st.header("👤 Step 5: About You")
        age_group = st.selectbox("1️⃣1️⃣ Your Age Group", ["", "18–30", "31–50", "51–70", "70+"])
        role = st.text_input("Your Role", help="Farmer, Healer, Grandparent, Herbalist, Teacher, Student, etc.")
        user_name = st.text_input("Your Name")
        contact_info = st.text_input("Contact Info (Email/Phone)")
        consent = st.radio("1️⃣2️⃣ Do You Give Permission to Use This Data?", [
            "Yes, I give permission (anonymously)", "No, keep private"
        ])

        if st.button("📤 Submit Your Contribution"):
            # Validate the required fields
            missing_fields = []
            
            if not plant_name:
                missing_fields.append("Plant name")
            if not voice_note:
                missing_fields.append("Voice recording")
            if not notes_scan:
                missing_fields.append("Handwritten or printed notes")
            if not age_group or age_group == "":
                missing_fields.append("Age group")
            if not role:
                missing_fields.append("Your role")
            if not user_name:
                missing_fields.append("Your name")
            if not contact_info:
                missing_fields.append("Contact information")
            
            if missing_fields:
                st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
            else:
                st.success("Thank you for sharing your knowledge! Your input will help preserve traditional plant wisdom.")

                # Generate a unique ID for this submission
                submission_id = str(uuid.uuid4())[:8]
                submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.write("Submitted at:", submission_time)
                st.write("Submission ID:", submission_id)
            
            # File paths for uploaded media
            photo_path = ""
            voice_path = ""
            notes_path = ""
            
            # Save photo if uploaded
            if photo:
                file_ext = os.path.splitext(photo.name)[1]
                photo_path = f"uploads/photos/{submission_id}{file_ext}"
                try:
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())
                except Exception as e:
                    st.error(f"Error saving photo: {e}")
            
            # Save voice note if uploaded
            if voice_note:
                file_ext = os.path.splitext(voice_note.name)[1]
                voice_path = f"uploads/voice/{submission_id}{file_ext}"
                try:
                    with open(voice_path, "wb") as f:
                        f.write(voice_note.getbuffer())
                except Exception as e:
                    st.error(f"Error saving voice recording: {e}")
                    
            # Save notes scan if uploaded
            if notes_scan:
                file_ext = os.path.splitext(notes_scan.name)[1]
                notes_path = f"uploads/notes/{submission_id}{file_ext}"
                try:
                    with open(notes_path, "wb") as f:
                        f.write(notes_scan.getbuffer())
                except Exception as e:
                    st.error(f"Error saving notes scan: {e}")

            # Add user information from session
            user_id = st.session_state.user_info['id'] if st.session_state.user_info else None
            submitter_name = st.session_state.user_info['name'] if st.session_state.user_info else user_name
            
            # Save structured data to CSV
            row = [submission_id, submission_time, plant_name, entry_title, local_names, scientific_name, 
                   ", ".join(category) if category else "", usage_desc, prep_method, community, tags,
                   location, language, lat, lon, age_group, role, submitter_name, contact_info, consent,
                   photo_path if photo else "", voice_path if voice_note else "", notes_path if notes_scan else "",
                   user_id]

            file_path = "plantspeak_submissions.csv"
            header = ["ID", "Time", "Plant Name", "Entry Title", "Local Names", "Scientific Name", "Category", 
                      "Usage Description", "Preparation Method", "Community", "Tags", "Location", "Language", 
                      "Latitude", "Longitude", "Age Group", "Role", "Name", "Contact", "Consent",
                      "Photo Path", "Voice Path", "Notes Path", "User ID"]
                      
            # Store in SQLite database
            db_save_success = save_submission_to_db(
                submission_id, user_id, submission_time, plant_name, entry_title, local_names, scientific_name,
                ", ".join(category) if category else "", usage_desc, prep_method, community, tags,
                location, language, lat, lon, photo_path, voice_path, notes_path, 
                age_group, role, user_name, contact_info, consent
            )
            
            if db_save_success:
                st.success("Submission saved to database successfully")
            else:
                st.warning("Note: Your submission was saved locally but there was an issue with the database. An administrator has been notified.")
            
            # Also save to CSV for backwards compatibility
            if not os.path.exists(file_path):
                with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerow(row)
            else:
                with open(file_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

        # Display uploaded content
        if photo:
            st.image(photo, caption="Uploaded Plant Photo", use_column_width=True)
            st.success(f"Photo saved as {os.path.basename(photo_path)}")

        if notes_scan:
            if notes_scan.type == "application/pdf":
                st.write("PDF uploaded: ", notes_scan.name)
                st.success(f"Notes saved as {os.path.basename(notes_path)}")
            else:
                st.image(notes_scan, caption="Scanned Notes", use_column_width=True)
                st.success(f"Notes saved as {os.path.basename(notes_path)}")

        if voice_note:
            st.audio(voice_note, format='audio/wav')
            st.success(f"Voice recording saved as {os.path.basename(voice_path)}")
            
        # Display summary of submission
        st.subheader("📋 Submission Summary")
        # Use current time for the summary if submission hasn't been made yet
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_data = {
            "Plant Name": plant_name,
            "Entry Title": entry_title if entry_title else "Not provided",
            "Categories": ", ".join(category) if category else "None selected",
            "Location": location if location else "Not provided",
            "Date & Time": current_time
        }
        st.json(summary_data)

    # Tab 2 - View Submissions
    if tab2 is not None:
        with tab2:
            st.title("📚 Past Submissions")
            
            # Load submissions from database
            # Get current user ID if logged in
            current_user_id = st.session_state.user_info['id'] if 'user_info' in st.session_state else None
            
            # Get submissions, filtered by privacy settings
            submissions_list = get_user_submissions(current_user_id)
            
            # Convert to dataframe for easier filtering
            if submissions_list:
                submissions_df = pd.DataFrame(submissions_list)
                
                # Add filtering options
                st.subheader("🔍 Filter Submissions")
                col1, col2, col3 = st.columns(3)
        
                with col1:
                    # Filter by category
                    all_categories = set()
                    for cats in submissions_df['category'].dropna():
                        for cat in cats.split(", "):
                            if cat:
                                all_categories.add(cat)
                    
                    selected_category = st.selectbox(
                        "Filter by Category", 
                        ["All"] + sorted(list(all_categories))
                    )
                
                with col2:
                    # Search by plant name or location
                    search_term = st.text_input("Search by Plant Name or Location")
                
                with col3:
                    # Filter by user
                    show_only_mine = st.checkbox("Show only my submissions", value=False)
                
                # Apply filters
                filtered_df = submissions_df.copy()
                
                if selected_category and selected_category != "All":
                    filtered_df = filtered_df[filtered_df['category'].str.contains(selected_category, na=False)]
                    
                if search_term:
                    name_matches = filtered_df['plant_name'].str.contains(search_term, case=False, na=False)
                    location_matches = filtered_df['location'].str.contains(search_term, case=False, na=False)
                    filtered_df = filtered_df[name_matches | location_matches]
                    
                if show_only_mine and st.session_state.user_info:
                    filtered_df = filtered_df[filtered_df['user_id'] == st.session_state.user_info['id']]
                    
                # Show filtered results
                st.subheader(f"Showing {len(filtered_df)} submissions")
                
                # Display a more user-friendly version of the dataframe
                display_df = filtered_df[['id', 'plant_name', 'entry_title', 'scientific_name', 
                                         'category', 'location', 'submission_time', 'submitter_name']]
                display_df.columns = ['ID', 'Plant Name', 'Title', 'Scientific Name', 
                                     'Category', 'Location', 'Date & Time', 'Submitted By']
                st.dataframe(display_df)
                
                # Display selected entry
                if not filtered_df.empty:
                    st.subheader("📖 View Details")
                    submission_ids = filtered_df['id'].tolist()
                    submission_names = [f"{row['plant_name']} ({row['id']})" for _, row in filtered_df.iterrows()]
                    selected_idx = st.selectbox("Select a submission to view details", 
                                              range(len(submission_ids)),
                                              format_func=lambda i: submission_names[i])
                    
                    if selected_idx is not None:
                        selected_id = submission_ids[selected_idx]
                        entry = filtered_df[filtered_df['id'] == selected_id].iloc[0]
                        
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            # Display plant name and privacy status
                            title_col, status_col = st.columns([3, 1])
                            with title_col:
                                st.subheader(f"{entry['plant_name']}")
                            with status_col:
                                if pd.notna(entry['consent']) and entry['consent'] == 'No, keep private':
                                    st.warning("🔒 Private")
                                else:
                                    st.success("🌍 Public")
                            
                            if pd.notna(entry['entry_title']):
                                st.write(f"**Title:** {entry['entry_title']}")
                            st.write(f"**Scientific Name:** {entry['scientific_name']}")
                            st.write(f"**Categories:** {entry['category']}")
                            st.write(f"**Local Names:** {entry['local_names']}")
                            st.write(f"**Community:** {entry['community']}")
                            st.write(f"**Location:** {entry['location']}")
                            st.write(f"**Submitted By:** {entry['submitter_name'] if pd.notna(entry['submitter_name']) else 'Anonymous'}")
                            st.write(f"**Date:** {entry['submission_time']}")
                
                            with detail_col2:
                                if pd.notna(entry['photo_path']) and os.path.exists(entry['photo_path']):
                                    st.image(entry['photo_path'], caption="Plant Photo")
                            
                            st.subheader("Description")
                            st.write(f"**Usage:** {entry['usage_desc']}")
                            st.write(f"**Preparation:** {entry['prep_method']}")
                            
                            # Display contributor information if available
                            if pd.notna(entry['age_group']) or pd.notna(entry['submitter_role']):
                                st.subheader("Contributor Information")
                                if pd.notna(entry['age_group']):
                                    st.write(f"**Age Group:** {entry['age_group']}")
                                if pd.notna(entry['submitter_role']):
                                    st.write(f"**Role:** {entry['submitter_role']}")
                                if pd.notna(entry['submitter_name']) and entry['submitter_name'] != entry['submitter_name']:
                                    st.write(f"**Name:** {entry['submitter_name']}")
                                # Contact info is only displayed to the owner of the submission
                                current_user_id = st.session_state.user_info['id'] if 'user_info' in st.session_state else None
                                
                                # Show privacy status and contact info if authorized
                                if pd.notna(entry['consent']):
                                    st.write(f"**Consent:** {entry['consent']}")
                                    
                                # Only show contact info to the owner of the submission
                                if current_user_id and str(current_user_id) == str(entry.get('user_id')):
                                    if pd.notna(entry['contact_info']):
                                        st.write(f"**Contact:** {entry['contact_info']}")
                            
                            # Display other media if available
                            st.subheader("Attachments")
                            if pd.notna(entry['voice_path']) and os.path.exists(entry['voice_path']):
                                st.write("**Voice Recording:**")
                                st.audio(entry['voice_path'])
                            
                            if pd.notna(entry['notes_path']) and os.path.exists(entry['notes_path']):
                                if entry['notes_path'].endswith('.pdf'):
                                    st.write(f"[View PDF Notes]({entry['notes_path']})")
                                else:
                                    st.image(entry['notes_path'], caption="Scanned Notes")

                # Download link for the CSV file
                def download_link(df, file_name):
                    csv_df = df[['id', 'plant_name', 'entry_title', 'scientific_name', 'category', 
                               'local_names', 'usage_desc', 'prep_method', 'location', 'submission_time']]
                    csv = csv_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">Download CSV File</a>'
                    return href
                
                st.markdown(download_link(filtered_df, "plantspeak_filtered_data.csv"), unsafe_allow_html=True)
                
            else:
                st.info("No submissions in the database yet. Add your first plant knowledge entry using the 'Add New Entry' tab.")
                
                # Try to import existing CSV data if available
                if os.path.exists("plantspeak_submissions.csv"):
                    st.info("Legacy CSV data found. Would you like to import it to the database?")
                    if st.button("Import CSV Data to Database"):
                        with st.spinner("Importing data..."):
                            try:
                                csv_df = pd.read_csv("plantspeak_submissions.csv")
                                import_count = 0
                                
                                for _, row in csv_df.iterrows():
                                    # Map CSV columns to database fields
                                    submission_id = row.get('ID', str(uuid.uuid4())[:8])
                                    user_id = row.get('User ID', None)
                                    
                                    db_save_success = save_submission_to_db(
                                        submission_id, user_id, row.get('Time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                        row.get('Plant Name', ''), row.get('Entry Title', ''), 
                                        row.get('Local Names', ''), row.get('Scientific Name', ''),
                                        row.get('Category', ''), row.get('Usage Description', ''), 
                                        row.get('Preparation Method', ''), row.get('Community', ''), 
                                        row.get('Tags', ''), row.get('Location', ''), row.get('Language', ''),
                                        row.get('Latitude', 0.0), row.get('Longitude', 0.0),
                                        row.get('Photo Path', ''), row.get('Voice Path', ''), 
                                        row.get('Notes Path', ''), row.get('Age Group', ''),
                                        row.get('Role', ''), row.get('Name', ''),
                                        row.get('Contact', ''), row.get('Consent', '')
                                    )
                                    
                                    if db_save_success:
                                        import_count += 1
                                
                                st.success(f"Successfully imported {import_count} submissions from CSV to the database!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error importing data: {e}")

def update_user_profile(user_id, name=None, email=None, role=None, community=None, password=None):
    """Update user profile information in the database"""
    conn = sqlite3.connect('plantspeak.db')
    c = conn.cursor()
    
    update_fields = []
    params = []
    
    # Build the update query based on which fields are provided
    if name is not None:
        update_fields.append("name = ?")
        params.append(name)
    if email is not None:
        update_fields.append("email = ?")
        params.append(email)
    if role is not None:
        update_fields.append("role = ?")
        params.append(role)
    if community is not None:
        update_fields.append("community = ?")
        params.append(community)
    if password is not None:
        update_fields.append("password = ?")
        params.append(hash_password(password))
    
    # If there are fields to update
    if update_fields:
        # Add user_id to the params
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            c.execute(query, params)
            conn.commit()
            success = True
        except sqlite3.IntegrityError as e:
            # Most likely due to duplicate email
            print(f"Database update error: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    conn.close()
    return False  # No fields to update
