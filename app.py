import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

# --- CONFIG & DATA ---
st.set_page_config(page_title="Indian Food Health Suite", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('enriched_food_metadata_english.csv')
    df.fillna(0, inplace=True)
    return df

df = load_data()

# Helper to find the correct image path
def get_image_path(food_name):
    # Match your flat zip naming: folder_name.jpg
    clean_name = food_name.replace(' ', '_')
    possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    for ext in possible_extensions:
        path = os.path.join("images", f"{clean_name}{ext}")
        if os.path.exists(path):
            return path
    return None

# --- LOGIC ---
def get_health_analysis(row):
    try:
        p, c, f, cal = float(row['Protein (g)']), float(row['Carbs (g)']), float(row['Fat (g)']), float(row['Calories (kcal)'])
        if cal <= 0: return 5.0, "NEUTRAL", "#9E9E9E", "Ensure fresh ingredients."
        raw_score = (p * 2.0) - (f * 1.8) - (cal / 100)
        score = round(max(0, min(10, 6.0 + (raw_score / 5))), 1)
        
        if score >= 8.0: return score, "SUPER FOOD", "#1B5E20", "Excellent choice!"
        elif score >= 6.0: return score, "HEALTHY", "#2E7D32", "Great balance."
        elif score >= 4.0: return score, "BALANCED", "#FBC02D", "Watch portions."
        else: return score, "INDULGENT", "#D84315", "Try air-frying."
    except: return 5.0, "UNKNOWN", "#9E9E9E", "Data unavailable."

def create_pdf(food_name):
    row = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(row)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # 1. Add Image to PDF if exists
    img_path = get_image_path(food_name)
    if img_path:
        elements.append(RLImage(img_path, width=200, height=150))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<font color='#2E7D32' size=20><b>{food_name.upper()}</b></font>", styles['Title']))
    elements.append(Paragraph(f"Health Rating: {score}/10 ({label})", styles['Normal']))
    elements.append(Spacer(1, 10))
    
    data = [['Nutrient', 'Value'], 
            ['Calories', f"{row['Calories (kcal)']} kcal"], 
            ['Protein', f"{row['Protein (g)']}g"],
            ['Carbs', f"{row['Carbs (g)']}g"],
            ['Fat', f"{row['Fat (g)']}g"]]
    
    t = Table(data, colWidths=[100, 100])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.green), 
                           ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                           ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    
    doc.build(elements)
    return buffer.getvalue()

# --- STREAMLIT UI ---
st.title("🍲 Indian Food Smart Health Suite")

with st.sidebar:
    search_query = st.text_input("🔍 Search Food")
    filtered_df = df[df['food_name'].str.contains(search_query, case=False)] if search_query else df
    food_name = st.selectbox("🍱 Select Dish", filtered_df['food_name'].unique())
    calorie_goal = st.slider("🎯 Daily kcal Goal", 100, 2000, 500)

if food_name:
    item = df[df['food_name'] == food_name].iloc[0]
    col1, col2 = st.columns([1, 1])

    with col1:
        # 2. Display Image on Dashboard
        img_path = get_image_path(food_name)
        if img_path:
            st.image(img_path, use_container_width=True)
        else:
            st.warning("📸 No image found in 'images/' folder.")

        cal_val = float(item['Calories (kcal)'])
        if cal_val > 0:
            grams = round((calorie_goal / cal_val) * 100)
            st.info(f"⚖️ To stay under **{calorie_goal} kcal**, limit portion to **{grams}g**.")
        
    with col2:
        score, label, color, tip = get_health_analysis(item)
        st.metric("Health Score", f"{score}/10", label)
        st.write(f"💡 *{tip}*")
        
        # Plotting
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.barh(['Protein', 'Carbs', 'Fat'], 
                [item['Protein (g)'], item['Carbs (g)'], item['Fat (g)']], 
                color=['#2E7D32', '#FBC02D', '#D84315'])
        st.pyplot(fig)
        
        pdf_bytes = create_pdf(food_name)
        st.download_button(label="📥 Download Recipe PDF", 
                           data=pdf_bytes, 
                           file_name=f"{food_name}_recipe.pdf", 
                           mime="application/pdf")
