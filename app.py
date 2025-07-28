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

# Language translations dictionary
LANGUAGES = {
    'English': {
        'app_title': '🌿 PlantSpeak – Preserve Plant Knowledge',
        'select_language': 'Select Language / भाषा चुनें / భాష ఎంచుకోండి',
        'login': 'Login',
        'register': 'Register',
        'login_header': '🔑 Login to PlantSpeak',
        'register_header': '📝 Create an Account',
        'username': 'Username',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'full_name': 'Full Name (optional)',
        'email': 'Email (optional)',
        'role': 'Role (e.g., Farmer, Healer, Researcher)',
        'community': 'Community or Organization',
        'login_button': '🔓 Login',
        'register_button': '✅ Register',
        'logout_button': '🚪 Logout',
        'welcome': 'Welcome',
        'navigation': 'Navigation',
        'add_entry': '📝 Add Entry',
        'view_submissions': '📚 View Submissions',
        'my_profile': '👤 My Profile',
        'invalid_credentials': 'Invalid username or password',
        'passwords_not_match': 'Passwords do not match',
        'password_too_short': 'Password must be at least 6 characters long',
        'username_required': 'Username and password are required',
        'registration_successful': 'Registration successful! Please login.',
        'username_exists': 'Username already exists',
        'email_exists': 'Email already exists',
        # Main form translations
        'app_main_title': '🌿 PlantSpeak – Help Us Preserve Traditional Plant Knowledge',
        'app_description': 'Many elders, farmers, and healers hold deep knowledge about local plants — used in remedies, rituals, and daily life. This app helps collect, preserve, and share that knowledge.',
        'step1_header': '📥 Step 1: Upload or Identify the Plant',
        'upload_photo': '📸 Upload a photo of the plant (leaf, flower, bark, etc.)',
        'plant_name_input': '✍️ Enter the Name of the Plant (in any language)',
        'entry_title_input': '📝 Entry Title (Optional)',
        'step2_header': '🧾 Step 2: Share What You Know',
        'local_names_input': '1️⃣ Local Name(s) of the Plant',
        'scientific_name_input': '2️⃣ Scientific / Botanical Name (Optional)',
        'category_select': '3️⃣ Category of Use',
        'usage_desc_input': '4️⃣ Describe the Use of the Plant',
        'prep_method_input': '5️⃣ Explain the Preparation or Application Process',
        'community_input': '6️⃣ Who Uses This Plant in Your Area?',
        'tags_input': '🔖 Tags or Keywords (Optional)',
        'step3_header': '🌍 Step 3: Location & Language',
        'location_input': '7️⃣ Where is this Plant Found or Used?',
        'language_input': '8️⃣ Language or Dialect You\'re Using',
        'step4_header': '🎤 Step 4: Voice & Text Extras',
        'voice_upload': '9️⃣ Upload a Voice Recording',
        'notes_upload': '🔠 10️⃣ Upload Handwritten or Printed Notes',
        'step5_header': '👤 Step 5: About You',
        'age_group_select': '1️⃣1️⃣ Your Age Group',
        'submit_button': '📤 Submit Your Contribution'
    },
    'हिंदी': {
        'app_title': '🌿 प्लांटस्पीक – पारंपरिक पौधों का ज्ञान संरक्षित करें',
        'select_language': 'भाषा चुनें / Select Language / భాష ఎంచుకోండి',
        'login': 'लॉगिन',
        'register': 'रजिस्टर करें',
        'login_header': '🔑 प्लांटस्पीक में लॉगिन करें',
        'register_header': '📝 खाता बनाएं',
        'username': 'उपयोगकर्ता नाम',
        'password': 'पासवर्ड',
        'confirm_password': 'पासवर्ड की पुष्टि करें',
        'full_name': 'पूरा नाम (वैकल्पिक)',
        'email': 'ईमेल (वैकल्पिक)',
        'role': 'भूमिका (जैसे किसान, वैद्य, शोधकर्ता)',
        'community': 'समुदाय या संगठन',
        'login_button': '🔓 लॉगिन',
        'register_button': '✅ रजिस्टर',
        'logout_button': '🚪 लॉगआउट',
        'welcome': 'स्वागत है',
        'navigation': 'नेवीगेशन',
        'add_entry': '📝 नई प्रविष्टि जोड़ें',
        'view_submissions': '📚 सबमिशन देखें',
        'my_profile': '👤 मेरी प्रोफ़ाइल',
        'invalid_credentials': 'गलत उपयोगकर्ता नाम या पासवर्ड',
        'passwords_not_match': 'पासवर्ड मेल नहीं खाते',
        'password_too_short': 'पासवर्ड कम से कम 6 अक्षर का होना चाहिए',
        'username_required': 'उपयोगकर्ता नाम और पासवर्ड आवश्यक है',
        'registration_successful': 'पंजीकरण सफल! कृपया लॉगिन करें।',
        'username_exists': 'उपयोगकर्ता नाम पहले से मौजूद है',
        'email_exists': 'ईमेल पहले से मौजूद है',
        # Main form translations
        'app_main_title': '🌿 प्लांटस्पीक – पारंपरिक पौधों के ज्ञान को संरक्षित करने में हमारी मदद करें',
        'app_description': 'कई बुजुर्गों, किसानों और वैद्यों के पास स्थानीय पौधों के बारे में गहरा ज्ञान है — जो उपचार, अनुष्ठान और दैनिक जीवन में उपयोग होता है। यह ऐप उस ज्ञान को एकत्र, संरक्षित और साझा करने में मदद करता है।',
        'step1_header': '📥 चरण 1: पौधे की तस्वीर अपलोड करें या पहचानें',
        'upload_photo': '📸 पौधे की तस्वीर अपलोड करें (पत्ती, फूल, छाल, आदि)',
        'plant_name_input': '✍️ पौधे का नाम दर्ज करें (किसी भी भाषा में)',
        'entry_title_input': '📝 प्रविष्टि शीर्षक (वैकल्पिक)',
        'step2_header': '🧾 चरण 2: अपना ज्ञान साझा करें',
        'local_names_input': '1️⃣ पौधे के स्थानीय नाम',
        'scientific_name_input': '2️⃣ वैज्ञानिक / वनस्पति नाम (वैकल्पिक)',
        'category_select': '3️⃣ उपयोग की श्रेणी',
        'usage_desc_input': '4️⃣ पौधे के उपयोग का वर्णन करें',
        'prep_method_input': '5️⃣ तैयारी या प्रयोग की प्रक्रिया बताएं',
        'community_input': '6️⃣ आपके क्षेत्र में यह पौधा कौन उपयोग करता है?',
        'tags_input': '🔖 टैग या कीवर्ड (वैकल्पिक)',
        'step3_header': '🌍 चरण 3: स्थान और भाषा',
        'location_input': '7️⃣ यह पौधा कहाँ पाया या उपयोग किया जाता है?',
        'language_input': '8️⃣ आपकी भाषा या बोली',
        'step4_header': '🎤 चरण 4: आवाज और पाठ अतिरिक्त',
        'voice_upload': '9️⃣ आवाज की रिकॉर्डिंग अपलोड करें',
        'notes_upload': '🔠 10️⃣ हस्तलिखित या मुद्रित नोट्स अपलोड करें',
        'step5_header': '👤 चरण 5: आपके बारे में',
        'age_group_select': '1️⃣1️⃣ आपका आयु समूह',
        'submit_button': '📤 अपना योगदान सबमिट करें'
    },
    'తెలుగు': {
        'app_title': '🌿 ప్లాంట్‌స్పీక్ – సాంప్రదాయ మొక్కల జ్ఞానాన్ని భద్రపరచండి',
        'select_language': 'భాష ఎంచుకోండి / Select Language / भाषा चुनें',
        'login': 'లాగిన్',
        'register': 'రిజిస్టర్',
        'login_header': '🔑 ప్లాంట్‌స్పీక్‌లో లాగిన్ చేయండి',
        'register_header': '📝 ఖాతా సృష్టించండి',
        'username': 'వినియోగదారు పేరు',
        'password': 'పాస్‌వర్డ్',
        'confirm_password': 'పాస్‌వర్డ్ నిర్ధారించండి',
        'full_name': 'పూర్తి పేరు (ఐచ్ఛికం)',
        'email': 'ఇమెయిల్ (ఐచ్ఛికం)',
        'role': 'పాత్ర (ఉదా: రైతు, వైద్యుడు, పరిశోధకుడు)',
        'community': 'సమాజం లేదా సంస్థ',
        'login_button': '🔓 లాగిన్',
        'register_button': '✅ రిజిస్టర్',
        'logout_button': '🚪 లాగ్‌అవుట్',
        'welcome': 'స్వాగతం',
        'navigation': 'నావిగేషన్',
        'add_entry': '📝 కొత్త ఎంట్రీ జోడించండి',
        'view_submissions': '📚 సబ్మిషన్లను చూడండి',
        'my_profile': '👤 నా ప్రొఫైల్',
        'invalid_credentials': 'తప్పుడు వినియోగదారు పేరు లేదా పాస్‌వర్డ్',
        'passwords_not_match': 'పాస్‌వర్డ్లు సరిపోలలేదు',
        'password_too_short': 'పాస్‌వర్డ్ కనీసం 6 అక్షరాలు ఉండాలి',
        'username_required': 'వినియోగదారు పేరు మరియు పాస్‌వర్డ్ అవసరం',
        'registration_successful': 'రిజిస్ట్రేషన్ విజయవంతం! దయచేసి లాగిన్ చేయండి.',
        'username_exists': 'వినియోగదారు పేరు ఇప్పటికే ఉంది',
        'email_exists': 'ఇమెయిల్ ఇప్పటికే ఉంది',
        # Main form translations
        'app_main_title': '🌿 ప్లాంట్‌స్పీక్ – సాంప్రదాయ మొక్కల జ్ఞానాన్ని భద్రపరచడంలో మాకు సహాయపడండి',
        'app_description': 'చాలా మంది పెద్దలు, రైతులు మరియు వైద్యులకు స్థానిక మొక్కల గురించి లోతైన జ్ఞానం ఉంది — వైద్యం, ఆచారాలు మరియు దైనందిన జీవితంలో ఉపయోగించబడుతుంది. ఈ యాప్ ఆ జ్ఞానాన్ని సేకరించి, భద్రపరచి మరియు పంచుకోవడంలో సహాయపడుతుంది.',
        'step1_header': '📥 దశ 1: మొక్క యొక్క చిత్రాన్ని అప్‌లోడ్ చేయండి లేదా గుర్తించండి',
        'upload_photo': '📸 మొక్క యొక్క చిత్రాన్ని అప్‌లోడ్ చేయండి (ఆకు, పువ్వు, బెరడు, మొదలైనవి)',
        'plant_name_input': '✍️ మొక్క పేరును నమోదు చేయండి (ఏ భాషలో అయినా)',
        'entry_title_input': '📝 ప్రవేశ శీర్షిక (ఐచ్ఛికం)',
        'step2_header': '🧾 దశ 2: మీ జ్ఞానాన్ని పంచుకోండి',
        'local_names_input': '1️⃣ మొక్క యొక్క స్థానిక పేర్లు',
        'scientific_name_input': '2️⃣ శాస్త్రీయ / వృక్షశాస్త్ర పేరు (ఐచ్ఛికం)',
        'category_select': '3️⃣ ఉపయోగ వర్గం',
        'usage_desc_input': '4️⃣ మొక్క యొక్క ఉపయోగాన్ని వివరించండి',
        'prep_method_input': '5️⃣ తయారీ లేదా అప్లికేషన్ ప్రక్రియను వివరించండి',
        'community_input': '6️⃣ మీ ప్రాంతంలో ఈ మొక్కను ఎవరు ఉపయోగిస్తారు?',
        'tags_input': '🔖 ట్యాగ్‌లు లేదా కీవర్డ్‌లు (ఐచ్ఛికం)',
        'step3_header': '🌍 దశ 3: స్థానం మరియు భాష',
        'location_input': '7️⃣ ఈ మొక్క ఎక్కడ దొరుకుతుంది లేదా ఉపయోగించబడుతుంది?',
        'language_input': '8️⃣ మీ భాష లేదా మాండలికం',
        'step4_header': '🎤 దశ 4: వాయిస్ మరియు టెక్స్ట్ అదనపు',
        'voice_upload': '9️⃣ వాయిస్ రికార్డింగ్ అప్‌లోడ్ చేయండి',
        'notes_upload': '🔠 10️⃣ చేతితో వ్రాసిన లేదా ముద్రించిన గమనికలను అప్‌లోడ్ చేయండి',
        'step5_header': '👤 దశ 5: మీ గురించి',
        'age_group_select': '1️⃣1️⃣ మీ వయో వర్గం',
        'submit_button': '📤 మీ సహకారాన్ని సమర్పించండి'
    },
    'தமிழ்': {
        'app_title': '🌿 பிளாண்ட்ஸ்பீக் – பாரம்பரிய தாவர அறிவைப் பாதுகாக்கவும்',
        'select_language': 'மொழியைத் தேர்ந்தெடுக்கவும் / Select Language / भाषा चुनें',
        'login': 'உள்நுழைவு',
        'register': 'பதிவு',
        'login_header': '🔑 பிளாண்ட்ஸ்பீக்கில் உள்நுழையவும்',
        'register_header': '📝 கணக்கை உருவாக்கவும்',
        'username': 'பயனர் பெயர்',
        'password': 'கடவுச்சொல்',
        'confirm_password': 'கடவுச்சொல்லை உறுதிப்படுத்தவும்',
        'full_name': 'முழு பெயர் (விருப்பமானது)',
        'email': 'மின்னஞ்சல் (விருப்பமானது)',
        'role': 'பங்கு (எ.கா: விவசாயி, மருத்துவர், ஆராய்ச்சியாளர்)',
        'community': 'சமுதாயம் அல்லது அமைப்பு',
        'login_button': '🔓 உள்நுழைவு',
        'register_button': '✅ பதிவு',
        'logout_button': '🚪 வெளியேறு',
        'welcome': 'வரவேற்கிறோம்',
        'navigation': 'வழிசெலுத்தல்',
        'add_entry': '📝 புதிய பதிவு சேர்க்கவும்',
        'view_submissions': '📚 சமர்ப்பணங்களைப் பார்க்கவும்',
        'my_profile': '👤 எனது சுயவிவரம்',
        'invalid_credentials': 'தவறான பயனர் பெயர் அல்லது கடவுச்சொல்',
        'passwords_not_match': 'கடவுச்சொற்கள் பொருந்தவில்லை',
        'password_too_short': 'கடவுச்சொல் குறைந்தபட்சம் 6 எழுத்துகள் இருக்க வேண்டும்',
        'username_required': 'பயனர் பெயர் மற்றும் கடவுச்சொல் தேவை',
        'registration_successful': 'பதிவு வெற்றிகரமாக! தயவுசெய்து உள்நுழையவும்.',
        'username_exists': 'பயனர் பெயர் ஏற்கனவே உள்ளது',
        'email_exists': 'மின்னஞ்சல் ஏற்கனவே உள்ளது',
        # Main form translations
        'app_main_title': '🌿 பிளாண்ட்ஸ்பீக் – பாரம்பரிய தாவர அறிவைப் பாதுகாக்க எங்களுக்கு உதவுங்கள்',
        'app_description': 'பல பெரியவர்கள், விவசாயிகள் மற்றும் மருத்துவர்கள் உள்ளூர் தாவரங்கள் பற்றிய ஆழமான அறிவைக் கொண்டுள்ளனர் — மருந்துகள், சடங்குகள் மற்றும் அன்றாட வாழ்க்கையில் பயன்படுத்தப்படுகின்றன. இந்த பயன்பாடு அந்த அறிவை சேகரித்து, பாதுகாத்து மற்றும் பகிர்ந்துகொள்ள உதவுகிறது.',
        'step1_header': '📥 படி 1: தாவரத்தின் படத்தை பதிவேற்றவும் அல்லது அடையாளம் காணவும்',
        'upload_photo': '📸 தாவரத்தின் படத்தை பதிவேற்றவும் (இலை, மலர், பட்டை, போன்றவை)',
        'plant_name_input': '✍️ தாவரத்தின் பெயரை உள்ளிடவும் (எந்த மொழியிலும்)',
        'entry_title_input': '📝 பதிவு தலைப்பு (விருப்பமானது)',
        'step2_header': '🧾 படி 2: உங்கள் அறிவைப் பகிருங்கள்',
        'local_names_input': '1️⃣ தாவரத்தின் உள்ளூர் பெயர்கள்',
        'scientific_name_input': '2️⃣ அறிவியல் / தாவரவியல் பெயர் (விருப்பமானது)',
        'category_select': '3️⃣ பயன்பாட்டின் வகை',
        'usage_desc_input': '4️⃣ தாவரத்தின் பயன்பாட்டை விவரிக்கவும்',
        'prep_method_input': '5️⃣ தயாரிப்பு அல்லது பயன்பாட்டு செயல்முறையை விளக்கவும்',
        'community_input': '6️⃣ உங்கள் பகுதியில் இந்த தாவரத்தை யார் பயன்படுத்துகிறார்கள்?',
        'tags_input': '🔖 குறிச்சொற்கள் அல்லது முக்கிய வார்த்தைகள் (விருப்பமானது)',
        'step3_header': '🌍 படி 3: இடம் மற்றும் மொழி',
        'location_input': '7️⃣ இந்த தாவரம் எங்கே காணப்படுகிறது அல்லது பயன்படுத்தப்படுகிறது?',
        'language_input': '8️⃣ உங்கள் மொழி அல்லது பேச்சுவழக்கு',
        'step4_header': '🎤 படி 4: குரல் மற்றும் உரை கூடுதல்',
        'voice_upload': '9️⃣ குரல் பதிவை பதிவேற்றவும்',
        'notes_upload': '🔠 10️⃣ கையால் எழுதப்பட்ட அல்லது அச்சிடப்பட்ட குறிப்புகளை பதிவேற்றவும்',
        'step5_header': '👤 படி 5: உங்களைப் பற்றி',
        'age_group_select': '1️⃣1️⃣ உங்கள் வயது குழு',
        'submit_button': '📤 உங்கள் பங்களிப்பை சமர்ப்பிக்கவும்'
    },
    'ಕನ್ನಡ': {
        'app_title': '🌿 ಪ್ಲಾಂಟ್‌ಸ್ಪೀಕ್ – ಸಾಂಪ್ರದಾಯಿಕ ಸಸ್ಯ ಜ್ಞಾನವನ್ನು ಸಂರಕ್ಷಿಸಿ',
        'select_language': 'ಭಾಷೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ / Select Language / भाषा चुनें',
        'login': 'ಲಾಗಿನ್',
        'register': 'ನೋಂದಣಿ',
        'login_header': '🔑 ಪ್ಲಾಂಟ್‌ಸ್ಪೀಕ್‌ಗೆ ಲಾಗಿನ್ ಮಾಡಿ',
        'register_header': '📝 ಖಾತೆಯನ್ನು ರಚಿಸಿ',
        'username': 'ಬಳಕೆದಾರ ಹೆಸರು',
        'password': 'ಪಾಸ್‌ವರ್ಡ್',
        'confirm_password': 'ಪಾಸ್‌ವರ್ಡ್ ಖಚಿತಪಡಿಸಿ',
        'full_name': 'ಪೂರ್ಣ ಹೆಸರು (ಐಚ್ಛಿಕ)',
        'email': 'ಇಮೇಲ್ (ಐಚ್ಛಿಕ)',
        'role': 'ಪಾತ್ರ (ಉದಾ: ರೈತ, ವೈದ್ಯ, ಸಂಶೋಧಕ)',
        'community': 'ಸಮುದಾಯ ಅಥವಾ ಸಂಸ್ಥೆ',
        'login_button': '🔓 ಲಾಗಿನ್',
        'register_button': '✅ ನೋಂದಣಿ',
        'logout_button': '🚪 ಲಾಗ್‌ಔಟ್',
        'welcome': 'ಸ್ವಾಗತ',
        'navigation': 'ನ್ಯಾವಿಗೇಶನ್',
        'add_entry': '📝 ಹೊಸ ಪ್ರವೇಶ ಸೇರಿಸಿ',
        'view_submissions': '📚 ಸಲ್ಲಿಕೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
        'my_profile': '👤 ನನ್ನ ಪ್ರೊಫೈಲ್',
        'invalid_credentials': 'ತಪ್ಪಾದ ಬಳಕೆದಾರ ಹೆಸರು ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್',
        'passwords_not_match': 'ಪಾಸ್‌ವರ್ಡ್‌ಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ',
        'password_too_short': 'ಪಾಸ್‌ವರ್ಡ್ ಕನಿಷ್ಠ 6 ಅಕ್ಷರಗಳಾಗಿರಬೇಕು',
        'username_required': 'ಬಳಕೆದಾರ ಹೆಸರು ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ಅಗತ್ಯ',
        'registration_successful': 'ನೋಂದಣಿ ಯಶಸ್ವಿ! ದಯವಿಟ್ಟು ಲಾಗಿನ್ ಮಾಡಿ.',
        'username_exists': 'ಬಳಕೆದಾರ ಹೆಸರು ಈಗಾಗಲೇ ಅಸ್ತಿತ್ವದಲ್ಲಿದೆ',
        'email_exists': 'ಇಮೇಲ್ ಈಗಾಗಲೇ ಅಸ್ತಿತ್ವದಲ್ಲಿದೆ',
        # Main form translations
        'app_main_title': '🌿 ಪ್ಲಾಂಟ್‌ಸ್ಪೀಕ್ – ಸಾಂಪ್ರದಾಯಿಕ ಸಸ್ಯ ಜ್ಞಾನವನ್ನು ಸಂರಕ್ಷಿಸಲು ನಮಗೆ ಸಹಾಯ ಮಾಡಿ',
        'app_description': 'ಅನೇಕ ಹಿರಿಯರು, ರೈತರು ಮತ್ತು ವೈದ್ಯರು ಸ್ಥಳೀಯ ಸಸ್ಯಗಳ ಬಗ್ಗೆ ಆಳವಾದ ಜ್ಞಾನವನ್ನು ಹೊಂದಿದ್ದಾರೆ — ಔಷಧಗಳು, ಆಚಾರಗಳು ಮತ್ತು ದೈನಂದಿನ ಜೀವನದಲ್ಲಿ ಬಳಸಲಾಗುತ್ತದೆ. ಈ ಅಪ್ಲಿಕೇಶನ್ ಆ ಜ್ಞಾನವನ್ನು ಸಂಗ್ರಹಿಸಲು, ಸಂರಕ್ಷಿಸಲು ಮತ್ತು ಹಂಚಿಕೊಳ್ಳಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.',
        'step1_header': '📥 ಹಂತ 1: ಸಸ್ಯದ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಅಥವಾ ಗುರುತಿಸಿ',
        'upload_photo': '📸 ಸಸ್ಯದ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (ಎಲೆ, ಹೂವು, ತೊಗಟೆ, ಇತ್ಯಾದಿ)',
        'plant_name_input': '✍️ ಸಸ್ಯದ ಹೆಸರನ್ನು ನಮೂದಿಸಿ (ಯಾವುದೇ ಭಾಷೆಯಲ್ಲಿ)',
        'entry_title_input': '📝 ಪ್ರವೇಶ ಶೀರ್ಷಿಕೆ (ಐಚ್ಛಿಕ)',
        'step2_header': '🧾 ಹಂತ 2: ನಿಮ್ಮ ಜ್ಞಾನವನ್ನು ಹಂಚಿಕೊಳ್ಳಿ',
        'local_names_input': '1️⃣ ಸಸ್ಯದ ಸ್ಥಳೀಯ ಹೆಸರುಗಳು',
        'scientific_name_input': '2️⃣ ವೈಜ್ಞಾನಿಕ / ಸಸ್ಯಶಾಸ್ತ್ರೀಯ ಹೆಸರು (ಐಚ್ಛಿಕ)',
        'category_select': '3️⃣ ಬಳಕೆಯ ವರ್ಗ',
        'usage_desc_input': '4️⃣ ಸಸ್ಯದ ಬಳಕೆಯನ್ನು ವಿವರಿಸಿ',
        'prep_method_input': '5️⃣ ತಯಾರಿಕೆ ಅಥವಾ ಅನ್ವಯ ಪ್ರಕ್ರಿಯೆಯನ್ನು ವಿವರಿಸಿ',
        'community_input': '6️⃣ ನಿಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿ ಈ ಸಸ್ಯವನ್ನು ಯಾರು ಬಳಸುತ್ತಾರೆ?',
        'tags_input': '🔖 ಟ್ಯಾಗ್‌ಗಳು ಅಥವಾ ಕೀವರ್ಡ್‌ಗಳು (ಐಚ್ಛಿಕ)',
        'step3_header': '🌍 ಹಂತ 3: ಸ್ಥಳ ಮತ್ತು ಭಾಷೆ',
        'location_input': '7️⃣ ಈ ಸಸ್ಯ ಎಲ್ಲಿ ಕಂಡುಬರುತ್ತದೆ ಅಥವಾ ಬಳಸಲಾಗುತ್ತದೆ?',
        'language_input': '8️⃣ ನಿಮ್ಮ ಭಾಷೆ ಅಥವಾ ಉಪಭಾಷೆ',
        'step4_header': '🎤 ಹಂತ 4: ಧ್ವನಿ ಮತ್ತು ಪಠ್ಯ ಹೆಚ್ಚುವರಿ',
        'voice_upload': '9️⃣ ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
        'notes_upload': '🔠 10️⃣ ಕೈಯಿಂದ ಬರೆದ ಅಥವಾ ಮುದ್ರಿತ ಟಿಪ್ಪಣಿಗಳನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
        'step5_header': '👤 ಹಂತ 5: ನಿಮ್ಮ ಬಗ್ಗೆ',
        'age_group_select': '1️⃣1️⃣ ನಿಮ್ಮ ವಯಸ್ಸಿನ ಗುಂಪು',
        'submit_button': '📤 ನಿಮ್ಮ ಕೊಡುಗೆಯನ್ನು ಸಲ್ಲಿಸಿ'
    },
    'मराठी': {
        'app_title': '🌿 प्लांटस्पीक – पारंपारिक वनस्पती ज्ञान जतन करा',
        'select_language': 'भाषा निवडा / Select Language / भाषा चुनें',
        'login': 'लॉगिन',
        'register': 'नोंदणी',
        'login_header': '🔑 प्लांटस्पीकमध्ये लॉगिन करा',
        'register_header': '📝 खाते तयार करा',
        'username': 'वापरकर्ता नाव',
        'password': 'पासवर्ड',
        'confirm_password': 'पासवर्डची पुष्टी करा',
        'full_name': 'पूर्ण नाव (पर्यायी)',
        'email': 'ईमेल (पर्यायी)',
        'role': 'भूमिका (उदा: शेतकरी, वैद्य, संशोधक)',
        'community': 'समुदाय किंवा संस्था',
        'login_button': '🔓 लॉगिन',
        'register_button': '✅ नोंदणी',
        'logout_button': '🚪 लॉगआउट',
        'welcome': 'स्वागत',
        'navigation': 'नेव्हिगेशन',
        'add_entry': '📝 नवीन एंट्री जोडा',
        'view_submissions': '📚 सबमिशन पहा',
        'my_profile': '👤 माझे प्रोफाइल',
        'invalid_credentials': 'चुकीचे वापरकर्ता नाव किंवा पासवर्ड',
        'passwords_not_match': 'पासवर्ड जुळत नाहीत',
        'password_too_short': 'पासवर्ड किमान 6 अक्षरांचा असावा',
        'username_required': 'वापरकर्ता नाव आणि पासवर्ड आवश्यक',
        'registration_successful': 'नोंदणी यशस्वी! कृपया लॉगिन करा.',
        'username_exists': 'वापरकर्ता नाव आधीच अस्तित्वात आहे',
        'email_exists': 'ईमेल आधीच अस्तित्वात आहे',
        # Main form translations
        'app_main_title': '🌿 प्लांटस्पीक – पारंपारिक वनस्पती ज्ञान जतन करण्यासाठी आम्हाला मदत करा',
        'app_description': 'अनेक वडील, शेतकरी आणि वैद्य यांच्याकडे स्थानिक वनस्पतींबद्दल सखोल ज्ञान आहे — औषधे, विधी आणि दैनंदिन जीवनात वापरले जाते. हे अ‍ॅप त्या ज्ञानाचे संकलन, संरक्षण आणि साझाकरण करण्यात मदत करते.',
        'step1_header': '📥 पायरी 1: वनस्पतीचे छायाचित्र अपलोड करा किंवा ओळखा',
        'upload_photo': '📸 वनस्पतीचे छायाचित्र अपलोड करा (पान, फूल, साल, इत्यादी)',
        'plant_name_input': '✍️ वनस्पतीचे नाव प्रविष्ट करा (कोणत्याही भाषेत)',
        'entry_title_input': '📝 एंट्री शीर्षक (पर्यायी)',
        'step2_header': '🧾 पायरी 2: तुमचे ज्ञान सामायिक करा',
        'local_names_input': '1️⃣ वनस्पतीची स्थानिक नावे',
        'scientific_name_input': '2️⃣ वैज्ञानिक / वनस्पतिशास्त्रीय नाव (पर्यायी)',
        'category_select': '3️⃣ वापराची श्रेणी',
        'usage_desc_input': '4️⃣ वनस्पतीच्या वापराचे वर्णन करा',
        'prep_method_input': '5️⃣ तयारी किंवा वापराची प्रक्रिया स्पष्ट करा',
        'community_input': '6️⃣ तुमच्या भागात ही वनस्पती कोण वापरते?',
        'tags_input': '🔖 टॅग किंवा कीवर्ड (पर्यायी)',
        'step3_header': '🌍 पायरी 3: स्थान आणि भाषा',
        'location_input': '7️⃣ ही वनस्पती कुठे सापडते किंवा वापरली जाते?',
        'language_input': '8️⃣ तुमची भाषा किंवा बोली',
        'step4_header': '🎤 पायरी 4: आवाज आणि मजकूर अतिरिक्त',
        'voice_upload': '9️⃣ आवाज रेकॉर्डिंग अपलोड करा',
        'notes_upload': '🔠 10️⃣ हस्तलिखित किंवा मुद्रित नोट्स अपलोड करा',
        'step5_header': '👤 पायरी 5: तुमच्याबद्दल',
        'age_group_select': '1️⃣1️⃣ तुमचा वयोगट',
        'submit_button': '📤 तुमचे योगदान सबमिट करा'
    },
    'മലയാളം': {
        'app_title': '🌿 പ്ലാന്റ്‌സ്പീക്ക് – പരമ്പരാഗത സസ്യ അറിവ് സംരക്ഷിക്കുക',
        'select_language': 'ഭാഷ തിരഞ്ഞെടുക്കുക / Select Language / भाषा चुनें',
        'login': 'ലോഗിൻ',
        'register': 'രജിസ്റ്റർ',
        'login_header': '🔑 പ്ലാന്റ്‌സ്പീക്കിൽ ലോഗിൻ ചെയ്യുക',
        'register_header': '📝 അക്കൗണ്ട് സൃഷ്ടിക്കുക',
        'username': 'ഉപയോക്തൃനാമം',
        'password': 'പാസ്‌വേഡ്',
        'confirm_password': 'പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക',
        'full_name': 'പൂർണ്ണ നാമം (ഓപ്ഷണൽ)',
        'email': 'ഇമെയിൽ (ഓപ്ഷണൽ)',
        'role': 'പങ്ക് (ഉദാ: കർഷകൻ, വൈദ്യൻ, ഗവേഷകൻ)',
        'community': 'കമ്മ്യൂണിറ്റി അല്ലെങ്കിൽ സംഘടന',
        'login_button': '🔓 ലോഗിൻ',
        'register_button': '✅ രജിസ്റ്റർ',
        'logout_button': '🚪 ലോഗൗട്ട്',
        'welcome': 'സ്വാഗതം',
        'navigation': 'നാവിഗേഷൻ',
        'add_entry': '📝 പുതിയ എൻട്രി ചേർക്കുക',
        'view_submissions': '📚 സബ്മിഷനുകൾ കാണുക',
        'my_profile': '👤 എന്റെ പ്രൊഫൈൽ',
        'invalid_credentials': 'തെറ്റായ ഉപയോക്തൃനാമം അല്ലെങ്കിൽ പാസ്‌വേഡ്',
        'passwords_not_match': 'പാസ്‌വേഡുകൾ പൊരുത്തപ്പെടുന്നില്ല',
        'password_too_short': 'പാസ്‌വേഡ് കുറഞ്ഞത് 6 അക്ഷരമായിരിക്കണം',
        'username_required': 'ഉപയോക്തൃനാമവും പാസ്‌വേഡും ആവശ്യമാണ്',
        'registration_successful': 'രജിസ്ട്രേഷൻ വിജയകരം! ദയവായി ലോഗിൻ ചെയ്യുക.',
        'username_exists': 'ഉപയോക്തൃനാമം ഇതിനകം നിലവിലുണ്ട്',
        'email_exists': 'ഇമെയിൽ ഇതിനകം നിലവിലുണ്ട്',
        # Main form translations
        'app_main_title': '🌿 പ്ലാന്റ്‌സ്പീക്ക് – പരമ്പരാഗത സസ്യ അറിവ് സംരക്ഷിക്കാൻ ഞങ്ങളെ സഹായിക്കുക',
        'app_description': 'പല മുതിർന്നവർക്കും കർഷകർക്കും വൈദ്യർക്കും പ്രാദേശിക സസ്യങ്ങളെക്കുറിച്ച് അഗാധമായ അറിവുണ്ട് — മരുന്നുകൾ, ആചാരങ്ങൾ, ദൈനംദിന ജീവിതത്തിൽ ഉപയോഗിക്കുന്നവ. ഈ ആപ്പ് ആ അറിവ് ശേഖരിക്കാനും സംരക്ഷിക്കാനും പങ്കിടാനും സഹായിക്കുന്നു.',
        'step1_header': '📥 ഘട്ടം 1: സസ്യത്തിന്റെ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക അല്ലെങ്കിൽ തിരിച്ചറിയുക',
        'upload_photo': '📸 സസ്യത്തിന്റെ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക (ഇല, പൂവ്, പുറംതോട്, മുതലായവ)',
        'plant_name_input': '✍️ സസ്യത്തിന്റെ പേര് നൽകുക (ഏത് ഭാഷയിലും)',
        'entry_title_input': '📝 എൻട്രി തലക്കെട്ട് (ഓപ്ഷണൽ)',
        'step2_header': '🧾 ഘട്ടം 2: നിങ്ങളുടെ അറിവ് പങ്കിടുക',
        'local_names_input': '1️⃣ സസ്യത്തിന്റെ പ്രാദേശിക പേരുകൾ',
        'scientific_name_input': '2️⃣ ശാസ്ത്രീയ / സസ്യശാസ്ത്ര പേര് (ഓപ്ഷണൽ)',
        'category_select': '3️⃣ ഉപയോഗ വിഭാഗം',
        'usage_desc_input': '4️⃣ സസ്യത്തിന്റെ ഉപയോഗം വിവരിക്കുക',
        'prep_method_input': '5️⃣ തയ്യാറാക്കൽ അല്ലെങ്കിൽ പ്രയോഗ പ്രക്രിയ വിശദീകരിക്കുക',
        'community_input': '6️⃣ നിങ്ങളുടെ പ്രദേശത്ത് ഈ സസ്യം ആരാണ് ഉപയോഗിക്കുന്നത്?',
        'tags_input': '🔖 ടാഗുകൾ അല്ലെങ്കിൽ കീവേഡുകൾ (ഓപ്ഷണൽ)',
        'step3_header': '🌍 ഘട്ടം 3: സ്ഥലവും ഭാഷയും',
        'location_input': '7️⃣ ഈ സസ്യം എവിടെ കാണപ്പെടുന്നു അല്ലെങ്കിൽ ഉപയോഗിക്കുന്നു?',
        'language_input': '8️⃣ നിങ്ങളുടെ ഭാഷ അല്ലെങ്കിൽ പ്രാദേശിക ഭാഷ',
        'step4_header': '🎤 ഘട്ടം 4: ശബ്ദവും ടെക്സ്റ്റും അധിക',
        'voice_upload': '9️⃣ ശബ്ദ റെക്കോർഡിംഗ് അപ്‌ലോഡ് ചെയ്യുക',
        'notes_upload': '🔠 10️⃣ കൈയെഴുത്ത് അല്ലെങ്കിൽ അച്ചടിച്ച കുറിപ്പുകൾ അപ്‌ലോഡ് ചെയ്യുക',
        'step5_header': '👤 ഘട്ടം 5: നിങ്ങളെക്കുറിച്ച്',
        'age_group_select': '1️⃣1️⃣ നിങ്ങളുടെ പ്രായ വിഭാഗം',
        'submit_button': '📤 നിങ്ങളുടെ സംഭാവന സമർപ്പിക്കുക'
    }
}

# Function to get translation
def get_text(key, lang='English'):
    """Get translated text based on selected language"""
    return LANGUAGES.get(lang, LANGUAGES['English']).get(key, key)

# Initialize language in session state
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'English'

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

# Initialize language in session state first
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'English'

st.set_page_config(
    page_title=get_text('app_title', st.session_state.selected_language), 
    layout="wide"
)

# Check login status
is_logged_in = check_login_status()

# Initialize page selection in session state if not present
if 'page' not in st.session_state:
    st.session_state.page = 'login' if not is_logged_in else 'main'

# Sidebar navigation when logged in
if is_logged_in:
    st.sidebar.title(f"👤 {get_text('welcome', st.session_state.selected_language)}, {st.session_state.username}!")
    
    # Language selector in sidebar
    st.sidebar.subheader("🌍 Language / भाषा / భాష")
    language_options = ['English', 'हिंदी', 'తెలుగు', 'தமிழ்', 'ಕನ್ನಡ', 'मराठी', 'മലയാളം']
    selected_lang = st.sidebar.selectbox(
        "Choose language:",
        language_options,
        index=language_options.index(st.session_state.selected_language)
    )
    
    # Update language if changed
    if selected_lang != st.session_state.selected_language:
        st.session_state.selected_language = selected_lang
        st.rerun()
    
    # Navigation options
    st.sidebar.subheader(get_text('navigation', st.session_state.selected_language))
    page = st.sidebar.radio(
        "Go to:", 
        [
            get_text('add_entry', st.session_state.selected_language), 
            get_text('view_submissions', st.session_state.selected_language), 
            get_text('my_profile', st.session_state.selected_language)
        ]
    )
    
    # Map selection to session state
    if page == get_text('add_entry', st.session_state.selected_language):
        st.session_state.page = 'main'
    elif page == get_text('view_submissions', st.session_state.selected_language):
        st.session_state.page = 'submissions'
    elif page == get_text('my_profile', st.session_state.selected_language):
        st.session_state.page = 'profile'
    
    # Logout button
    if st.sidebar.button(get_text('logout_button', st.session_state.selected_language)):
        logout_user()
        st.session_state.page = 'login'
        st.rerun()

# Login/Register Interface when not logged in
if not is_logged_in:
    # Language selection at the top
    st.header("🌍 " + get_text('select_language', st.session_state.selected_language))
    
    # Create columns for language selection
    lang_cols = st.columns(7)
    language_options = ['English', 'हिंदी', 'తెలుగు', 'தமிழ்', 'ಕನ್ನಡ', 'मराठी', 'മലയാളം']
    
    for i, lang in enumerate(language_options):
        with lang_cols[i]:
            if st.button(lang, key=f"lang_{lang}"):
                st.session_state.selected_language = lang
                st.rerun()
    
    # Display current language selection
    st.info(f"Selected Language / चुनी गई भाषा / ఎంచుకున్న భాష: **{st.session_state.selected_language}**")
    
    # Choose between login and registration with translated text
    login_tab, register_tab = st.tabs([
        f"🔑 {get_text('login', st.session_state.selected_language)}", 
        f"📝 {get_text('register', st.session_state.selected_language)}"
    ])
    
    with login_tab:
        st.header(get_text('login_header', st.session_state.selected_language))
        
        login_username = st.text_input(
            get_text('username', st.session_state.selected_language), 
            key="login_username"
        )
        login_password = st.text_input(
            get_text('password', st.session_state.selected_language), 
            type="password", 
            key="login_password"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            login_button = st.button(get_text('login_button', st.session_state.selected_language))
        
        if login_button:
            if authenticate_user(login_username, login_password):
                login_user(login_username)
                st.session_state.page = 'main'
                st.success(f"{get_text('welcome', st.session_state.selected_language)}, {login_username}!")
                st.rerun()
            else:
                st.error(get_text('invalid_credentials', st.session_state.selected_language))
    
    with register_tab:
        st.header(get_text('register_header', st.session_state.selected_language))
        
        reg_username = st.text_input(
            get_text('username', st.session_state.selected_language) + " (required)", 
            key="reg_username"
        )
        reg_password = st.text_input(
            get_text('password', st.session_state.selected_language) + " (required)", 
            type="password", 
            key="reg_password"
        )
        reg_password_confirm = st.text_input(
            get_text('confirm_password', st.session_state.selected_language), 
            type="password", 
            key="reg_password_confirm"
        )
        
        reg_name = st.text_input(get_text('full_name', st.session_state.selected_language), key="reg_name")
        reg_email = st.text_input(get_text('email', st.session_state.selected_language), key="reg_email")
        reg_role = st.text_input(get_text('role', st.session_state.selected_language), key="reg_role")
        reg_community = st.text_input(get_text('community', st.session_state.selected_language), key="reg_community")
        
        register_button = st.button(get_text('register_button', st.session_state.selected_language))
        
        if register_button:
            # Basic validation with translated error messages
            if not reg_username or not reg_password:
                st.error(get_text('username_required', st.session_state.selected_language))
            elif reg_password != reg_password_confirm:
                st.error(get_text('passwords_not_match', st.session_state.selected_language))
            elif len(reg_password) < 6:
                st.error(get_text('password_too_short', st.session_state.selected_language))
            elif reg_email and not re.match(r"[^@]+@[^@]+\.[^@]+", reg_email):
                st.error("Please enter a valid email address")  # Keep in English as it's technical
            else:
                if add_user(reg_username, reg_password, reg_name, reg_email, reg_role, reg_community):
                    st.success(get_text('registration_successful', st.session_state.selected_language))
                    # Auto-login after registration
                    login_user(reg_username)
                    st.session_state.page = 'main'
                    st.rerun()
                else:
                    st.error(get_text('username_exists', st.session_state.selected_language))

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
                    st.rerun()
                else:
                    st.error("Failed to update profile. The email may already be in use.")
        
## Only proceed with content tabs if we're on a page that has them and tabs are created
if not is_logged_in:
    # Not logged in: show nothing (login/register UI is already shown above)
    pass
elif tab1 is not None and st.session_state.page not in ['profile']:
    # Tab 1 - Add New Entry
    with tab1:
        st.title(get_text('app_main_title', st.session_state.selected_language))

        st.markdown(get_text('app_description', st.session_state.selected_language))
        
        st.header(get_text('step1_header', st.session_state.selected_language))
        photo = st.file_uploader(get_text('upload_photo', st.session_state.selected_language), type=["jpg", "jpeg", "png"])
        plant_name = st.text_input(get_text('plant_name_input', st.session_state.selected_language))
        entry_title = st.text_input(get_text('entry_title_input', st.session_state.selected_language), help="A title for your submission")

        st.header(get_text('step2_header', st.session_state.selected_language))
        local_names = st.text_area(get_text('local_names_input', st.session_state.selected_language), help="List local names in various languages or dialects")
        scientific_name = st.text_input(get_text('scientific_name_input', st.session_state.selected_language))

        category = st.multiselect(get_text('category_select', st.session_state.selected_language), [
            "Medicinal", "Food / Cooking", "Religious / Ritual",
            "Ecological / Environmental", "Craft / Utility", "Other"
        ])

        usage_desc = st.text_area(get_text('usage_desc_input', st.session_state.selected_language), help="E.g., Used to treat fever, offered in rituals, made into tea")
        prep_method = st.text_area(get_text('prep_method_input', st.session_state.selected_language), help="How is it prepared, how much is used, and how often?")
        community = st.text_input(get_text('community_input', st.session_state.selected_language), help="Mention tribe, village, or community")
        tags = st.text_input(get_text('tags_input', st.session_state.selected_language), help="Separate by commas, e.g. headache, fever, forest plant")

        st.header(get_text('step3_header', st.session_state.selected_language))
        location = st.text_input(get_text('location_input', st.session_state.selected_language), help="Village, District, State")
        language = st.text_input(get_text('language_input', st.session_state.selected_language))

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
                            st.rerun()
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
                                    st.rerun()
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
                                st.rerun()
        
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
        st.header(get_text('step4_header', st.session_state.selected_language))
        voice_note = st.file_uploader(get_text('voice_upload', st.session_state.selected_language), type=["mp3", "wav", "m4a"])
        notes_scan = st.file_uploader(get_text('notes_upload', st.session_state.selected_language), type=["jpg", "jpeg", "png", "pdf"])

        # Step 5: About You
        st.header(get_text('step5_header', st.session_state.selected_language))
        age_group = st.selectbox(get_text('age_group_select', st.session_state.selected_language), ["", "18–30", "31–50", "51–70", "70+"])
        role = st.text_input("Your Role", help="Farmer, Healer, Grandparent, Herbalist, Teacher, Student, etc.")
        user_name = st.text_input("Your Name")
        contact_info = st.text_input("Contact Info (Email/Phone)")
        consent = st.radio("1️⃣2️⃣ Do You Give Permission to Use This Data?", [
            "Yes, I give permission (anonymously)", "No, keep private"
        ])

        if st.button(get_text('submit_button', st.session_state.selected_language)):
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
                                st.rerun()
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
