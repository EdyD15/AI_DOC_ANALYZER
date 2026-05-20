# Styles for the Streamlit app

cyberpunk_styles = """
<style>
/* 1. Global Setup & Background */
.stApp {
    background-color: #090A0F;
    color: #E2E8F0;
}

/* 2. Main Layout Container - Centered and properly width-constrained */
.main .block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 900px !important;
    margin: 0 auto !important;
    padding-top: 40px !important;
}

/* 3. Center main header and subtitle with Cyberpunk Gradient */
.stApp h1, 
[data-testid="stHeaderElement"] h1, 
.stMarkdown h1 {
    text-align: center !important;
    margin: 0 auto !important;
    display: block !important;
    width: 100% !important;
    background: linear-gradient(135deg, #00F5D4 0%, #3D5AFE 50%, #7B2CBF 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 46px !important;
    font-weight: 800 !important;
    padding-top: 20px !important;
}

.stCaption, 
.stCaption p {
    text-align: center !important;
    margin: 0 auto !important;
    display: block !important;
    width: 100% !important;
    color: #3D5AFE !important;
}

/* 4. Blend the Sidebar Background */
[data-testid="stSidebar"] {
    background-color: #090A0F;
    border-right: 1px solid #1E293B;
    transition: all 0.3s ease;
}

/* 5. Redesign Sidebar Buttons with smooth 0.3s transition */
[data-testid="stSidebar"] button {
    background-color: transparent !important;
    border: none !important;
    color: #94A3B8 !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.3s ease !important; /* Aici este efectul de tranzitie graduala */
}

[data-testid="stSidebar"] button:hover,
[data-testid="stSidebar"] button:active,
[data-testid="stSidebar"] button:focus {
    background-color: #3D5AFE !important;
    color: #FFFFFF !important;
}

/* 6. Fix Chat Bubbles - Left aligned, properly spaced, Neon Glow */
.chat-row {
    padding: 18px 20px !important;
    margin-bottom: 20px !important;
    border-radius: 12px !important;
    display: block !important;
    text-align: left !important;
    animation: fadeInSlideUp 0.4s ease forwards;
}

/* Force all text inside bubbles to stay left and have breathing room */
.chat-row * {
    text-align: left !important;
}

.chat-row p {
    margin-top: 8px !important;
    margin-bottom: 0 !important;
    line-height: 1.6 !important;
}

.user-row {
    background-color: #0D0E12 !important;
    border: 1px solid #00F5D4 !important;
    box-shadow: 0 0 15px rgba(0, 245, 212, 0.25) !important;
}

.ai-row {
    background-color: #0D0E12 !important;
    border: 1px solid #7B2CBF !important;
    box-shadow: 0 0 15px rgba(123, 44, 191, 0.25) !important;
}

/* 7. Hide default Streamlit elements */
header, footer, .stApp > div:first-child > div:first-child > div:first-child {
    display: none;
}

/* 8. Fix Chat Input Bar - Full width outer border and glowing focus */
[data-testid="stBottomBlockContainer"] {
    background-color: #090A0F;
}

div[data-testid="stChatInput"] [data-testid="baseButton-secondary"] {
    display: none !important;
}

div[data-testid="stChatInput"] {
    background-color: #0D0E12 !important;
    border: 1px solid #262930 !important;
    border-radius: 12px !important;
    padding: 4px 8px !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: #3D5AFE !important;
    box-shadow: 0 0 15px rgba(61, 90, 254, 0.3) !important;
}

div[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: none !important;
}

/* 9. Seamless File Uploader with Dashed Blue Neon */
div[data-testid="stFileUploader"] {
    background-color: transparent !important;
    border: none !important;
}

div[data-testid="stFileUploaderDropzone"] {
    background-color: #0D0E12 !important;
    border: 1px dashed #3D5AFE !important;
    border-radius: 12px !important;
    box-shadow: 0 0 10px rgba(61, 90, 254, 0.15) !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #00F5D4 !important;
    box-shadow: 0 0 15px rgba(0, 245, 212, 0.3) !important;
}

div[data-testid="stFileUploader"] label, 
div[data-testid="stFileUploader"] p, 
div[data-testid="stFileUploader"] small {
    color: #94A3B8 !important;
}

div[data-testid="stFileUploader"] button {
    background-color: #161923 !important;
    color: #FFFFFF !important;
    border: 1px solid #1E293B !important;
    transition: all 0.3s ease !important; /* Si aici este aplicata tranzitia graduala */
}

div[data-testid="stFileUploader"] button:hover {
    background-color: #3D5AFE !important;
}

/* Animations */
@keyframes fadeInSlideUp {
    0% {
        opacity: 0;
        transform: translateY(10px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
"""