# 🌿 PlantSpeak - Preserve Traditional Plant Knowledge

PlantSpeak is a Streamlit web application designed to collect and preserve traditional knowledge about plants and their uses in various communities.

## Features

- **User Authentication:** Secure login system with user accounts
- **Data Collection:** Collect comprehensive information about plants including names, uses, preparation methods, and more
- **Media Support:** Upload photos, voice recordings, and document scans
- **Database Storage:** Save all entries to both SQLite database and CSV files
- **Geographic Information:** Auto-detect location, reverse geocode coordinates, and visualize on maps
- **Browse Submissions:** View, filter, and search past submissions
- **User Profiles:** Track your contributions and update your profile

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the App

Start the application with the following command:
```
streamlit run app.py
```

The app will be available in your web browser at 'https://plantspeak-7yrxhom64ucrsfzkh8jcwj.streamlit.app/'

## Data Storage

- Submitted data is stored in `plantspeak_submissions.csv`
- Uploaded media is stored in the `uploads/` directory

## Usage

1. **Register/Login**: Create a new account or login with existing credentials
2. **Add Entry**: Navigate to the "Add New Entry" tab to submit information about a plant
3. **Fill Information**: Enter plant details, uses, and preparation methods
4. **Location**: Use the location auto-detection feature to record where the plant was found
5. **Media Upload**: Add photos, audio recordings, or document scans
6. **Submit**: Save your contribution to the database
7. **Browse**: Use the "View Submissions" tab to search, filter, and download past entries
8. **Profile**: View your contributions and manage your account information

## Privacy Note

The location detection feature uses:
- IP-based geolocation (approximate)
- OpenStreetMap's Nominatim API for reverse geocoding

This data is only saved locally in your CSV file and is not shared with any third parties other than the API services used for detection. If precise location is a concern, you can manually enter coordinates or location names.
