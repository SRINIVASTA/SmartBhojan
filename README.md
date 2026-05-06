# 🍲 Smart Bhojan: Personalized Nutrition & Recipe Dashboard


**Smart Bhojan** is a Streamlit-based web application designed to help users understand the nutritional profile of Indian dishes. It calculates a custom health score, visualizes macronutrients, and provides downloadable PDF recipe reports.

## 🔗 Live Demo
Check out the live app here: [**Smart Bhojan Web App**](https://smartbhojan-9hebtsjz3wun3adggzry6s.streamlit.app/)

## 🚀 Features
- **Health Scoring Engine:** Uses a custom algorithm to rate food from 0-10 (Super Food to Indulgent).
- **Nutritional Visualization:** Horizontal bar charts showing Protein, Carbs, and Fat content.
- **Dynamic Search:** Filter through dishes using the sidebar search and selection tools.
- **PDF Report Generator:** Export recipes and nutritional facts into a professionally formatted PDF with custom borders.
- **Responsive UI:** Custom CSS "Green Frame" design for a clean, modern aesthetic.

## 🛠️ Tech Stack
- **Frontend:** [Streamlit](https://streamlit.io)
- **Data Handling:** Pandas
- **Visualization:** Matplotlib
- **PDF Generation:** ReportLab
- **Styling:** Custom CSS & HTML Injection

## 📂 Project Structure
```text
├── app.py                # Main Streamlit application code
├── enriched_food_metadata_english.csv  # Food dataset (Names, Macros, Instructions)
├── images/               # Folder containing food images (e.g., Panner_Tikka.jpg)
└── README.md             # Project documentation
```

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd smart-bhojan
   ```

2. **Install dependencies:**
   ```bash
   pip install streamlit pandas matplotlib reportlab
   ```

3. **Prepare your Data:**
   - Ensure your `enriched_food_metadata_english.csv` includes columns: `food_name`, `Protein (g)`, `Carbs (g)`, `Fat (g)`, `Calories (kcal)`, and `Instructions`.
   - Place images in the `images/` folder with names matching the `food_name` (e.g., `samosa.jpg`).

4. **Run the App Locally:**
   ```bash
   streamlit run app.py
   ```

## 💡 How it Works
The health score is calculated based on a weighted formula:
`Score = 6.0 + [(Protein * 2.5) - (Fat * 1.5) - (Calories / 100)] / 5`
This rewards high protein content while penalizing excessive fats and empty calories.

### Created by Srinivasta 🥗 🥘 🍱 🥞 🥙
