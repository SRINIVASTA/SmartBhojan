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

# --- CUSTOM CSS FOR BORDER ---
st.markdown("""
    <style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-border {
        border: 5px solid #2E7D32;
        padding: 30px;
        border-radius: 15px;
        background-color: white;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH): return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    df.fillna("N/A", inplace=True) # Ensure recipe text isn't empty
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

# --- PDF ENGINE WITH BORDER & RECIPE ---
def draw_border(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.darkgreen)
    canvas.setLineWidth(3)
    canvas.rect(25, 25, PAGE_WIDTH - 50, PAGE_HEIGHT - 50)
    canvas.restoreState()

def create_recipe_pdf(food_name):
    row = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(row)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=60)
    styles = getSampleStyleSheet()
    elements = []
    
    # Image
    img_path = get_image_path(food_name)
    if img_path:
        elements.append(RLImage(img_path, width=200, height=150))
    
    elements.append(Paragraph(f"<b>{food_name.upper()}</b>", styles['Title']))
    elements.append(Paragraph(f"Rating: {score}/10 ({label})", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    # Nutrition Table
    data = [['Nutrient', 'Value'], ['Calories', f"{row['Calories (kcal)']} kcal"], ['Protein', f"{row['Protein (g)']}g"], ['Carbs', f"{row['Carbs (g)']}g"], ['Fat', f"{row['Fat (g)']}g"]]
    t = Table(data, colWidths=[120, 120])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # 📝 RECIPE SECTION IN PDF
    elements.append(Paragraph("<b>RECIPE INSTRUCTIONS</b>", styles['Heading2']))
    recipe_text = str(row.get('Instructions', 'Recipe instructions not available.'))
    elements.append(Paragraph(recipe_text, styles['Normal']))
    
    doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)
    return buffer.getvalue()

# --- MAIN UI ---
# Sidebar is outside the border
with st.sidebar:
    st.header("⚙️ Settings")
    search = st.text_input("🔍 Search Food")
    filtered = sorted(df[df['food_name'].str.contains(search, case=False)]['food_name'].unique()) if not df.empty else []
    food_name = st.selectbox("🍱 Select Dish", filtered)
    goal = st.slider("🎯 kcal Goal", 100, 1500, 500)

# Main Dashboard wrapped in border
st.markdown('<div class="main-border">', unsafe_allow_html=True)

if food_name:
    item = df[df['food_name'] == food_name].iloc[0]
    st.header(f"🍲 {food_name}")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        img_path = get_image_path(food_name)
        if img_path: st.image(img_path, use_container_width=True)
        score, label, color, tip = get_health_analysis(item)
        st.metric("Health Rating", f"{score}/10", label)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.barh(['Protein', 'Carbs', 'Fat'], [float(item['Protein (g)']), float(item['Carbs (g)']), float(item['Fat (g)'])], color=['#2E7D32', '#FBC02D', '#D84315'])
        st.pyplot(fig)
        st.info(f"💡 {tip}")
        
    # 📝 RECIPE SECTION ON DESKTOP
    st.markdown("---")
    st.subheader("📖 Recipe & Instructions")
    st.write(item.get('Instructions', "Recipe not found in dataset."))
    
    st.download_button("📥 Download Full Report (PDF)", create_recipe_pdf(food_name), f"{food_name}.pdf", "application/pdf")

else:
    st.write("Please select a dish from the sidebar to begin.")

st.markdown('</div>', unsafe_allow_html=True)
