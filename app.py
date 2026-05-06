import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- CONFIGURATION ---
CSV_PATH = 'enriched_food_metadata_english.csv'
IMAGE_FOLDER = 'images'
PAGE_WIDTH, PAGE_HEIGHT = letter

st.set_page_config(page_title="Indian Food Health Suite", layout="wide")

# --- DESKTOP BORDER (CSS) ---
st.markdown("""
    <style>
    .main {
        border: 10px solid #2E7D32;
        padding: 20px;
        border-radius: 15px;
        margin: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH): return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    df.fillna(0, inplace=True)
    return df

df = load_data()

# --- LOGIC ---
def get_health_analysis(row):
    try:
        p, c, f, cal = float(row['Protein (g)']), float(row['Carbs (g)']), float(row['Fat (g)']), float(row['Calories (kcal)'])
        raw_score = (p * 2.0) - (f * 1.8) - (cal / 100)
        score = round(max(0, min(10, 6.0 + (raw_score / 5))), 1)
        if score >= 8.0: return score, "SUPER FOOD", "#1B5E20", "Excellent choice!"
        elif score >= 6.0: return score, "HEALTHY", "#2E7D32", "Great balance."
        elif score >= 4.0: return score, "BALANCED", "#FBC02D", "Watch portions."
        else: return score, "INDULGENT", "#D84315", "Try air-frying."
    except: return 5.0, "UNKNOWN", "#9E9E9E", "Data unavailable."

def get_image_path(food_name):
    clean_name = food_name.replace(' ', '_')
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        path = os.path.join(IMAGE_FOLDER, f"{clean_name}{ext}")
        if os.path.exists(path): return path
    return None

# --- PDF ENGINE WITH BORDER ---
def draw_border(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.darkgreen)
    canvas.setLineWidth(5)
    # Draw rectangle: (x, y, width, height)
    canvas.rect(20, 20, PAGE_WIDTH - 40, PAGE_HEIGHT - 40)
    canvas.setFont('Helvetica-Oblique', 8)
    canvas.drawCentredString(PAGE_WIDTH/2, 30, "✨ Indian Food Project - Nutrition Report ✨")
    canvas.restoreState()

def create_recipe_pdf(food_name):
    row = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(row)
    buffer = BytesIO()
    # Increased margins to fit inside the border
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=50, bottomMargin=50, leftMargin=50, rightMargin=50)
    styles = getSampleStyleSheet()
    elements = []
    
    img_path = get_image_path(food_name)
    if img_path:
        elements.append(RLImage(img_path, width=250, height=180))
    
    elements.append(Paragraph(f"<font color='#2E7D32' size=24><b>{food_name.upper()}</b></font>", styles['Title']))
    elements.append(Paragraph(f"⭐ Health Rating: {score}/10 ({label})", styles['Normal']))
    
    data = [['Nutrient', 'Value'], ['Calories', f"{row['Calories (kcal)']} kcal"], ['Protein', f"{row['Protein (g)']}g"], ['Carbs', f"{row['Carbs (g)']}g"], ['Fat', f"{row['Fat (g)']}g"]]
    table = Table(data, colWidths=[150, 150])
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(Spacer(1, 20)); elements.append(table); elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>Recipe Tips & Health Info:</b>", styles['Heading3']))
    elements.append(Paragraph(tip, styles['Normal']))
    
    # build PDF using the draw_border function on every page
    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)
    return buffer.getvalue()

# --- MAIN UI ---
st.markdown('<div class="main">', unsafe_allow_html=True) # Start Border Div

st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🍲 Indian Food Smart Health Suite</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    search_bar = st.text_input("🔍 Search food...")
    filtered_names = sorted(df[df['food_name'].str.contains(search_bar, case=False)]['food_name'].unique()) if not df.empty else []
    food_name = st.selectbox("🍱 Select Dish:", filtered_names) if filtered_names else None
    calorie_goal = st.slider("🎯 Target kcal:", 100, 2000, 500)

if food_name:
    item = df[df['food_name'] == food_name].iloc[0]
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        img_path = get_image_path(food_name)
        if img_path: st.image(img_path, use_container_width=True)
        st.info(f"⚖️ Portion Guide: Max **{round((calorie_goal / float(item['Calories (kcal)'])) * 100)}g** for {calorie_goal} kcal.")

    with col2:
        score, label, color, tip = get_health_analysis(item)
        st.metric("Health Score", f"{score}/10", label)
        
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.barh(['Protein', 'Carbs', 'Fat'], [float(item['Protein (g)']), float(item['Carbs (g)']), float(item['Fat (g)'])], color=['#2E7D32', '#FBC02D', '#D84315'])
        st.pyplot(fig)
        
        if st.download_button("📄 Download PDF Report", create_recipe_pdf(food_name), f"{food_name}_report.pdf", "application/pdf"):
            st.balloons()

st.markdown('</div>', unsafe_allow_html=True) # End Border Div
