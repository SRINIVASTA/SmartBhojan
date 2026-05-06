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

st.set_page_config(page_title="Smart Bhojan 🍲", layout="wide")

# --- REFINED CUSTOM CSS FOR VISIBILITY ---
st.markdown("""
    <style>
    /* 1. Reduce default Streamlit top whitespace */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
        border: 8px solid #2E7D32;
        border-radius: 30px;
        background-color: white;
        box-shadow: 15px 15px 35px rgba(0,0,0,0.1);
        margin-top: 10px;
    }
    
    /* 2. Fix Title Visibility & Styling */
    .smart-title {
        text-align: center;
        color: #2E7D32;
        font-family: 'Arial Black', Gadget, sans-serif;
        font-size: 50px;
        margin-top: 0px;
        padding-top: 0px;
        line-height: 1.2;
    }
    
    /* 3. Ensure Sidebar stays clean */
    [data-testid="stSidebar"] {
        background-color: #f1f3f4;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    if 'Instructions' not in df.columns:
        df['Instructions'] = "Recipe instructions not available."
    df.fillna(0, inplace=True)
    return df

df = load_data()

# --- ANALYSIS LOGIC ---
def get_health_analysis(row):
    try:
        p, c, f, cal = float(row['Protein (g)']), float(row['Carbs (g)']), float(row['Fat (g)']), float(row['Calories (kcal)'])
        raw_score = (p * 2.5) - (f * 1.5) - (cal / 100)
        score = round(max(0, min(10, 6.0 + (raw_score / 5))), 1)
        if score >= 8.0: return score, "SUPER FOOD", "#1B5E20", "Excellent choice!"
        elif score >= 6.0: return score, "HEALTHY", "#2E7D32", "Great balanced meal."
        elif score >= 4.0: return score, "BALANCED", "#FBC02D", "Watch portions."
        else: return score, "INDULGENT", "#D84315", "Try air-frying."
    except: return 5.0, "UNKNOWN", "#9E9E9E", "Data unavailable."

def get_image_path(food_name):
    clean_name = food_name.replace(' ', '_')
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        path = os.path.join(IMAGE_FOLDER, f"{clean_name}{ext}")
        if os.path.exists(path): return path
    return None

# --- PDF ENGINE ---
def draw_pdf_border(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.darkgreen)
    canvas.setLineWidth(4)
    canvas.rect(30, 30, PAGE_WIDTH - 60, PAGE_HEIGHT - 60)
    canvas.setFont('Helvetica-Bold', 14)
    canvas.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 45, "🍲 Smart Bhojan - Nutrition Report 🍲")
    canvas.restoreState()

def create_recipe_pdf(food_name):
    row = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(row)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=70, bottomMargin=70)
    styles = getSampleStyleSheet()
    elements = []
    
    img_path = get_image_path(food_name)
    if img_path: elements.append(RLImage(img_path, width=220, height=160))
    
    display_name = food_name.replace('_', ' ').title()
    elements.append(Paragraph(f"<b>DISH: {display_name}</b>", styles['Title']))
    elements.append(Paragraph(f"Health Score: {score}/10 ({label})", styles['Normal']))
    
    data = [['Nutrient', 'Per 100g'], ['Calories', f"{row['Calories (kcal)']} kcal"], ['Protein', f"{row['Protein (g)']}g"], ['Carbs', f"{row['Carbs (g)']}g"], ['Fat', f"{row['Fat (g)']}g"]]
    table = Table(data, colWidths=[120, 120])
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>📖 RECIPE INSTRUCTIONS</b>", styles['Heading2']))
    elements.append(Paragraph(str(row['Instructions']), styles['Normal']))
    
    doc.build(elements, onFirstPage=draw_pdf_border, onLaterPages=draw_pdf_border)
    return buffer.getvalue()

# --- UI LAYOUT ---
with st.sidebar:
    st.header("⚙️ App Settings")
    search_q = st.text_input("🔍 Search Food")
    options = sorted(df[df['food_name'].str.contains(search_q, case=False)]['food_name'].unique()) if search_q else sorted(df['food_name'].unique())
    food_choice = st.selectbox("🍱 Select Dish", options if options else ["No results"])
    kcal_goal = st.slider("🎯 Calories per Meal Goal", 100, 1500, 500)

# 1. Heading (Smart Bhojan)
st.markdown("<h1 class='smart-title'>🍲 Smart Bhojan 🍲</h1>", unsafe_allow_html=True)

if food_choice and food_choice != "No results":
    item = df[df['food_name'] == food_choice].iloc[0]
    score, label, color, tip = get_health_analysis(item)
    st.header(food_choice.replace('_', ' ').title())
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        img_path = get_image_path(food_choice)
        if img_path: st.image(img_path, use_container_width=True)
        st.metric("Health Score", f"{score}/10", label)

    with col2:
        st.subheader("Nutrition Profile")
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.barh(['Protein', 'Carbs', 'Fat'], [float(item['Protein (g)']), float(item['Carbs (g)']), float(item['Fat (g)'])], color=['#2E7D32', '#FBC02D', '#D84315'])
        st.pyplot(fig)
        st.info(f"💡 **Tip:** {tip}")
        st.download_button("📥 Download PDF Report", create_recipe_pdf(food_choice), f"SmartBhojan_{food_choice}.pdf", "application/pdf", use_container_width=True)

    st.markdown("---")
    st.subheader("📖 Recipe & Instructions")
    st.write(item['Instructions'])
else:
    st.info("👈 Please select a dish from the sidebar.")
