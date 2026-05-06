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

# --- CUSTOM CSS FOR FULL DESKTOP BORDER ---
st.markdown("""
    <style>
    /* Main container styling */
    .main-border {
        border: 6px solid #2E7D32;
        padding: 40px;
        border-radius: 25px;
        background-color: #ffffff;
        box-shadow: 10px 10px 30px rgba(0,0,0,0.1);
        min-height: 85vh;
        margin: 10px;
    }
    /* Title styling */
    .smart-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        text-align: center;
        color: #2E7D32;
        margin-bottom: 20px;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    # Ensure instructions column exists and is not NaN
    if 'Instructions' not in df.columns:
        df['Instructions'] = "Recipe instructions coming soon!"
    df.fillna({"Instructions": "No instructions available.", "Protein (g)": 0, "Carbs (g)": 0, "Fat (g)": 0, "Calories (kcal)": 0}, inplace=True)
    return df

df = load_data()

# --- LOGIC ---
def get_health_analysis(row):
    try:
        p, c, f, cal = float(row['Protein (g)']), float(row['Carbs (g)']), float(row['Fat (g)']), float(row['Calories (kcal)'])
        raw_score = (p * 2.5) - (f * 1.5) - (cal / 100)
        score = round(max(0, min(10, 6.0 + (raw_score / 5))), 1)
        
        if score >= 8.0: return score, "SUPER FOOD", "#1B5E20", "Excellent choice! Packed with nutrients."
        elif score >= 6.0: return score, "HEALTHY", "#2E7D32", "Great balance for a daily meal."
        elif score >= 4.0: return score, "BALANCED", "#FBC02D", "Watch portion sizes to maintain goals."
        else: return score, "INDULGENT", "#D84315", "Pro-Tip: Try air-frying or using minimal ghee."
    except: return 5.0, "UNKNOWN", "#9E9E9E", "Data unavailable."

def get_image_path(food_name):
    # Matches the 'food_name.jpg' or 'food_name.png' inside images folder
    clean_name = food_name.replace(' ', '_')
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        path = os.path.join(IMAGE_FOLDER, f"{clean_name}{ext}")
        if os.path.exists(path):
            return path
    return None

# --- PDF ENGINE ---
def draw_pdf_border(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.darkgreen)
    canvas.setLineWidth(4)
    # Draw the frame
    canvas.rect(30, 30, PAGE_WIDTH - 60, PAGE_HEIGHT - 60)
    # Footer
    canvas.setFont('Helvetica-Bold', 12)
    canvas.drawCentredString(PAGE_WIDTH/2, 45, "🍲 Smart Bhojan - Your Digital Nutrition Guide 🍲")
    canvas.restoreState()

def create_recipe_pdf(food_name):
    row = df[df['food_name'] == food_name].iloc[0]
    score, label, color, tip = get_health_analysis(row)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=60, bottomMargin=60)
    styles = getSampleStyleSheet()
    elements = []
    
    # 1. Branding Header
    elements.append(Paragraph("<font size=18 color='#2E7D32'><b>SMART BHOJAN REPORT</b></font>", styles['Title']))
    elements.append(Spacer(1, 10))
    
    # 2. Image
    img_path = get_image_path(food_name)
    if img_path:
        elements.append(RLImage(img_path, width=220, height=160))
        elements.append(Spacer(1, 12))
    
    # 3. Nutrition Title
    display_name = food_name.replace('_', ' ').title()
    elements.append(Paragraph(f"<b>Dish: {display_name}</b>", styles['Heading2']))
    elements.append(Paragraph(f"Health Score: {score}/10 ({label})", styles['Normal']))
    elements.append(Spacer(1, 10))
    
    # 4. Table
    data = [['Nutrient', 'Per 100g'], 
            ['Calories', f"{row['Calories (kcal)']} kcal"], 
            ['Protein', f"{row['Protein (g)']}g"], 
            ['Carbs', f"{row['Carbs (g)']}g"], 
            ['Fat', f"{row['Fat (g)']}g"]]
    
    table = Table(data, colWidths=[150, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgreen),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # 5. Recipe Instructions
    elements.append(Paragraph("<b>📖 RECIPE INSTRUCTIONS</b>", styles['Heading3']))
    recipe_text = str(row['Instructions'])
    elements.append(Paragraph(recipe_text, styles['Normal']))
    
    doc.build(elements, onFirstPage=draw_pdf_border, onLaterPages=draw_pdf_border)
    return buffer.getvalue()

# --- SIDEBAR (Outside the border) ---
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    search_query = st.text_input("🔍 Search Food", placeholder="e.g. Paneer")
    
    # Filter dropdown based on search
    if search_query:
        options = sorted(df[df['food_name'].str.contains(search_query, case=False)]['food_name'].unique())
    else:
        options = sorted(df['food_name'].unique())
        
    food_choice = st.selectbox("🍱 Select your Dish", options if options else ["No results"])
    kcal_slider = st.slider("🎯 Target kcal Goal", 100, 1500, 500, step=50)

# --- MAIN DASHBOARD (Inside the border) ---
st.markdown('<div class="main-border">', unsafe_allow_html=True)

# 1. Main Heading
st.markdown("<h1 class='smart-title'>🍲 Smart Bhojan 🍲</h1>", unsafe_allow_html=True)

if food_choice and food_choice != "No results":
    item = df[df['food_name'] == food_choice].iloc[0]
    score, label, color, tip = get_health_analysis(item)
    
    # Clean up name for display
    clean_display_name = food_choice.replace('_', ' ').title()
    st.header(clean_display_name)
    
    col1, col2 = st.columns([1, 1.3])
    
    with col1:
        # Display Image
        img_path = get_image_path(food_choice)
        if img_path:
            st.image(img_path, use_container_width=True, caption=f"Fresh {clean_display_name}")
        else:
            st.warning("📷 Image not found in images/ folder.")
            
        # Portion Guide
        cal_100 = float(item['Calories (kcal)'])
        if cal_100 > 0:
            allowed_grams = round((kcal_slider / cal_100) * 100)
            st.success(f"⚖️ **Portion Guide:** Stay under **{allowed_grams}g** to hit your **{kcal_slider} kcal** goal.")
            
        st.metric("Health Score", f"{score}/10", label)

    with col2:
        # Nutrition Bar Chart
        st.subheader("Nutrient Distribution (per 100g)")
        fig, ax = plt.subplots(figsize=(7, 3.5))
        nutrients = ['Protein', 'Carbs', 'Fat']
        values = [float(item['Protein (g)']), float(item['Carbs (g)']), float(item['Fat (g)'])]
        
        ax.barh(nutrients, values, color=['#2E7D32', '#FBC02D', '#D84315'])
        ax.set_xlabel('Grams (g)')
        st.pyplot(fig)
        
        st.info(f"💡 **Health Tip:** {tip}")
        
        # Download PDF Button
        pdf_data = create_recipe_pdf(food_choice)
        st.download_button(
            label="📥 Download Smart Bhojan Report (PDF)",
            data=pdf_data,
            file_name=f"SmartBhojan_{food_choice}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # 2. Recipe & Instructions Section
    st.markdown("---")
    st.subheader("📖 Recipe & Instructions")
    st.write(item['Instructions'])

else:
    st.info("👈 Use the sidebar to search and select a delicious Indian dish!")

st.markdown('</div>', unsafe_allow_html=True)
