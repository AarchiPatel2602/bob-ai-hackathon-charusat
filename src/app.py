import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="RouteWise AI", layout="wide", page_icon="🚢")

# Header
st.title("🚢 RouteWise AI - Supply Chain Disruption Assistant")
st.markdown("Powered by **IBM Bob & watsonx.ai**")
st.divider()

# Layout: Sidebar for Bob Copilot, Main for Dashboard
st.sidebar.header("🤖 IBM Bob Copilot")
st.sidebar.info("Status: Online | Connected to MCP Weather API & watsonx")

query = st.sidebar.text_area("Ask Bob about your supply chain:", placeholder="e.g. How does the hurricane affect our shipments?")

if st.sidebar.button("Ask Bob"):
    if query:
        st.sidebar.success("""
        **Bob's Analysis:**
        I found **3 shipments** affected by the incoming Category 3 hurricane on the East Coast. 
        
        **Recommendation:**
        Re-route Shipment `SHP-1042` (Vaccines) to Port of Miami immediately. This avoids a 48-hour delay and prevents $500K in temperature spoilage.
        """)
    else:
        st.sidebar.warning("Please enter a query.")

# Main Dashboard
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚨 Active Disruptions")
    st.error("**Hurricane Warning:** Category 3 storm approaching East Coast ports. Expected impact: 48-72 hours.")
    st.warning("**Port Strike:** 24-hour labor delay reported at Port of Los Angeles.")
    
    st.subheader("📍 Fleet Map (Simulated)")
    map_data = pd.DataFrame({
        'lat': [34.0522, 25.7617, 40.7128],
        'lon': [-118.2437, -80.1918, -74.0060]
    })
    st.map(map_data, zoom=3)

with col2:
    st.subheader("📦 At-Risk Shipments (Cold Chain IoT)")
    data = pd.DataFrame({
        "Shipment ID": ["SHP-1042", "SHP-2099", "SHP-3011", "SHP-4402"],
        "Contents": ["Vaccines", "Produce", "Electronics", "Pharmaceuticals"],
        "Destination": ["New York", "Los Angeles", "Miami", "Boston"],
        "IoT Status": ["Temp Warning (+2°C)", "Delayed", "On Track", "On Track"],
        "Risk Level": ["CRITICAL", "HIGH", "LOW", "LOW"]
    })
    
    st.dataframe(data, use_container_width=True)

st.divider()
st.caption("IBM BoB AI Innovation Hackathon 2026 - Demo Application")
