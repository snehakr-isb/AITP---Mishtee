import gradio as gr
import pandas as pd
import requests
from supabase import create_client, Client

# --- 1. ASSETS & CREDENTIALS ---
URL = "https://cvjoxzxishnjkdaarxdl.supabase.co"
KEY = "sb_publishable_wfZR4A_usCFZDGwQaz3PJg_9yPJW9bO"
LOGO_URL = "https://raw.githubusercontent.com/snehakr-isb/AITP---Mishtee/refs/heads/main/Google Gemini Generated Image.png"
STYLE_CSS_URL = "https://raw.githubusercontent.com/snehakr-isb/AITP---Mishtee/refs/heads/main/style.css"

supabase: Client = create_client(URL, KEY)

# High-End Minimalist CSS Skin
mishtee_css = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Inter:wght@300;400&display=swap');

.gradio-container { background-color: #FAF9F6 !important; font-family: 'Inter', sans-serif !important; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #333333 !important; letter-spacing: 0.05em !important; text-transform: uppercase; font-weight: 400 !important; text-align: center; }
.slogan { text-align: center; color: #C06C5C; font-style: italic; margin-top: -10px; margin-bottom: 30px; }

button.primary { 
    background-color: #C06C5C !important; 
    color: #FAF9F6 !important; 
    border-radius: 0px !important; 
    border: 1px solid #C06C5C !important; 
    box-shadow: none !important; 
    letter-spacing: 0.1em;
}

/* Sharp lines and minimalist padding */
* { border-radius: 0px !important; box-shadow: none !important; }
input, .table-wrap, table { border: 1px solid #333333 !important; }
"""

# --- 2. BACKEND FUNCTIONS ---

def fetch_trending_products():
    """Retrieves top 4 best-selling products by quantity."""
    response = supabase.table("orders").select("product_id, qty_kg").execute()
    if not response.data:
        return pd.DataFrame(columns=["Product", "Variant", "Total Sold (kg)"])

    df_orders = pd.DataFrame(response.data)
    trending_ids = df_orders.groupby("product_id")["qty_kg"].sum().reset_index()
    trending_ids = trending_ids.sort_values(by="qty_kg", ascending=False).head(4)

    trending_data = []
    for _, row in trending_ids.iterrows():
        p_id = int(row['product_id'])
        prod_info = supabase.table("products").select("sweet_name, variant_type").eq("item_id", p_id).execute()
        if prod_info.data:
            trending_data.append({
                "Product": prod_info.data[0]['sweet_name'],
                "Variant": prod_info.data[0]['variant_type'],
                "Total Sold (kg)": row['qty_kg']
            })
    return pd.DataFrame(trending_data)

def login_and_fetch_data(phone_number):
    """Processes customer login and returns greeting, history, and trending data."""
    # 1. Fetch Customer Info
    cust_res = supabase.table("customers").select("full_name").eq("phone", phone_number).execute()
    
    if not cust_res.data:
        greeting = "### Namaste! Welcome to MishTee-Magic. It looks like you're new to our world of purity."
        history_df = pd.DataFrame(columns=["Date", "Order ID", "Status", "Value (₹)"])
    else:
        name = cust_res.data[0]['full_name']
        greeting = f"### Namaste, {name} ji! Great to see you again."
        
        # 2. Fetch Order History
        order_res = supabase.table("orders").select("order_date, order_id, status, order_value_inr").eq("cust_phone", phone_number).execute()
        if order_res.data:
            history_df = pd.DataFrame(order_res.data)
            history_df.columns = ["Date", "Order ID", "Status", "Value (₹)"]
        else:
            history_df = pd.DataFrame(columns=["Date", "Order ID", "Status", "Value (₹)"])

    # 3. Fetch Trending Data (Universal)
    trending_df = fetch_trending_products()
    
    return greeting, history_df, trending_df

# --- 3. UI ASSEMBLY ---

with gr.Blocks(css=mishtee_css, title="MishTee-Magic") as demo:
    
    # Header Section
    with gr.Column():
        gr.Image(LOGO_URL, show_label=False, width=180, interactive=False, container=False)
        gr.Markdown("# MishTee-Magic")
        gr.Markdown("Purity and Health", elem_classes="slogan")

    # Welcome/Login Logic
    with gr.Row():
        with gr.Column(scale=2):
            phone_input = gr.Textbox(label="Access the Magic (Phone Number)", placeholder="91XXXXXXXX")
            login_btn = gr.Button("ENTER THE BOUTIQUE", variant="primary")
        with gr.Column(scale=3):
            greeting_output = gr.Markdown("### Welcome. Please log in to view your journey.")

    gr.HTML("<hr style='border: 0; border-top: 1px solid #333333; margin: 30px 0;'>")

    # Data Tables in Tabbed View
    with gr.Tabs():
        with gr.TabItem("MY ORDER HISTORY"):
            history_table = gr.Dataframe(
                headers=["Date", "Order ID", "Status", "Value (₹)"],
                datatype=["str", "str", "str", "number"],
                interactive=False
            )
        
        with gr.TabItem("TRENDING TODAY"):
            trending_table = gr.Dataframe(
                headers=["Product", "Variant", "Total Sold (kg)"],
                datatype=["str", "str", "number"],
                interactive=False
            )

    # Event Listener
    login_btn.click(
        fn=login_and_fetch_data,
        inputs=phone_input,
        outputs=[greeting_output, history_table, trending_table]
    )

if __name__ == "__main__":
    demo.launch()
