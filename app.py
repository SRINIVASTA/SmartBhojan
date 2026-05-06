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

st.set_page_config(page_title="Indian Food Health Suite", layout="wide")

# Load Data
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH):
        st.error(f"CSV file not found at {CSV_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    df.fillna(0, inplace=True)
    return df

df = load_data()

# --- CORE LOGIC ---
def get_health_analysis(row):
    try:
        p, c, f, cal = float(row['Protein (g)']), float(row['Carbs (g)']), float(row['Fat (g)']), float(row['Calories (kcal)'])
        if cal <= 0: return 5.0, "NEUTRAL", "#9E9E9E", "Ensure ingredients are fresh."
        raw_score = (p * 2.0) - (f * 1.8) - (cal / 100)
        score = round(max(0, min(10, 6.0 + (raw_score / 5))), 1)
        
        if score >= 8.0: return score, "SUPER FOOD", "#1B5E20", "Excellent choice! Pair with curd."
        elif score >= 6.0: return score, "HEALTHY", "#2E7D32", "Great balance. Use cold-pressed oils."
        elif score >= 4.0: return score, "BALANCED", "#FBC02D", "Watch portion sizes."
        else: return score, "INDULGENT", "#D84315", "Pro-Tip: Try air-frying or ghee in moderation."
    except: return 5.0, "UNKNOWN", "#9E9E9E", "Data unavailable."

def get_healthier_alternative(current_food_name):
    item = df[df['food_name'] == current_food_name].iloc[0]
    current_score, _, _, _ = get_health_analysis(item)
    temp_df = df.copy()
    temp_df['score'] = temp_df.apply(lambda x: get_health_analysis(x)[0], axis=1)
    better_options = temp_df[temp_df['score'] > current_score].sort_values(by='score', ascending=False)
    return better_options.iloc[0] if not better_options.empty else None

# Helper to find image
def get_image_path(food_name):
    clean_name = food_name.replace(' ', '_')
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        path = os.path.join(IMAGE_FOLDER, f"{clean_name}{ext}")
        if os.path.exists(path):
            return path
    return None

# --- PDF ENGINE ---
def create_recipe_pdf(food_name):
    row = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(row)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=25)
    styles = getSampleStyleSheet()
    elements = []
    
    img_path = get_image_path(food_name)
    if img_path:
        elements.append(RLImage(img_path, width=250, height=180))
    
    elements.append(Paragraph(f"<font color='#2E7D32' size=20><b>{food_name.upper()}</b></font>", styles['Title']))
    elements.append(Paragraph(f"⭐ Health Rating: {score}/10 ({label})", styles['Normal']))
    
    data = [['Nutrient', 'Per 100g'], 
            ['Calories', f"{row['Calories (kcal)']} kcal"], 
            ['Protein', f"{row['Protein (g)']}g"], 
            ['Carbs', f"{row['Carbs (g)']}g"], 
            ['Fat', f"{row['Fat (g)']}g"]]
    
    table = Table(data, colWidths=[150, 150])
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(Spacer(1, 10)); elements.append(table); elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("RECIPE INSTRUCTIONS", styles['Heading3']))
    elements.append(Paragraph(str(row.get('Instructions', 'N/A')), styles['Normal']))
    
    doc.build(elements)
    return buffer.getvalue()

# --- MAIN UI ---
st.markdown("<h1 style='color: #2E7D32;'>🍲 Indian Food Smart Health Suite</h1>", unsafe_allow_html=True)

# Sidebar Search & Selection
with st.sidebar:
    st.header("Search & Settings")
    search_bar = st.text_input("🔍 Search food name...")
    filtered_names = sorted(df[df['food_name'].str.contains(search_bar, case=False)]['food_name'].unique())
    
    if filtered_names:
        food_name = st.selectbox("🍱 Select Dish:", filtered_names)
    else:
        st.warning("No matches found.")
        food_name = None
        
    calorie_goal = st.slider("🎯 Target kcal per meal:", 100, 2000, 500, step=50)

# Main Dashboard
if food_name:
    item = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(item)
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        # 1. Image
        img_path = get_image_path(food_name)
        if img_path:
            st.image(img_path, caption=food_name, use_container_width=True)
        else:
            st.info("📸 No image available for this dish.")
            
        # 2. Portion Math
        cal_per_100g = float(item['Calories (kcal)'])
        if cal_per_100g > 0:
            max_grams = round((calorie_goal / cal_per_100g) * 100)
            st.success(f"⚖️ Portion Guide: To stay under **{calorie_goal} kcal**, limit portion to **{max_grams}g**.")

    with col2:
        # 3. Nutrition Chart
        st.subheader(f"Nutrition Profile ({food_name})")
        fig, ax = plt.subplots(figsize=(6, 3))
        labels = ['Protein', 'Carbs', 'Fat']
        vals = [float(item['Protein (g)']), float(item['Carbs (g)']), float(item['Fat (g)'])]
        bars = ax.barh(labels, vals, color=['#2E7D32', '#FBC02D', '#D84315'])
        ax.set_title(f"Energy: {item['Calories (kcal)']} kcal / 100g", fontsize=10)
        st.pyplot(fig)
        
        # 4. Metrics & Tips
        m1, m2 = st.columns(2)
        m1.metric("Health Score", f"{score}/10")
        m2.metric("Category", label)
        st.markdown(f"**💡 Pro-Tip:** {tip}")
        
        # 5. Alternatives
        alt = get_healthier_alternative(food_name)
        if alt is not None and score < 7.0:
            st.markdown(f"<p style='color: #1B5E20;'>🌟 <b>BETTER CHOICE:</b> Try <b>{alt['food_name'].upper()}</b> (Score: {get_health_analysis(alt)[0]}/10)</p>", unsafe_allow_html=True)

        # 6. PDF Download
        pdf_data = create_recipe_pdf(food_name)
        st.download_button(
            label="📄 Download Recipe & Nutrition PDF",
            data=pdf_data,
            file_name=f"{food_name.replace(' ', '_')}_report.pdf",
            mime="application/pdf"
        )
