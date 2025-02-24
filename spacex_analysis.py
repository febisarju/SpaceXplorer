import requests
import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px

# ---- CUSTOM CSS FOR SPACEX THEME ----
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF !important;
    }
    .stButton>button {
        background-color: #000000;
        color: #FFFFFF;
        border-radius: 5px;
        font-weight: bold;
    }
    .stSlider label {
        color: white !important;
    }
    .custom-box {
        text-align: center;
    }
    div[data-baseweb="select"] {
        margin-top: -40px;
    }
    div[data-baseweb="select"] * {
        cursor: pointer !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---- DASHBOARD TITLE ----
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcPUilyc66mOF_RtPn8c1MAJmeXUOOh__JQA&s", width=120)
with col2:
    st.markdown("""
        <div style="text-align: center; background-color: black; padding: 10px;">
            <h1>SpaceX Launch Dashboard</h1>
        </div> 
    """, unsafe_allow_html=True)

# ---- DATA FETCHING FUNCTION ----
@st.cache_data
def fetch_spacex_data():
    url = "https://api.spacexdata.com/v4/launches"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.json_normalize(data)
            st.markdown(f'<div class="custom-box">✓ MISSION DATA ACQUIRED: {len(df)} records</div>', unsafe_allow_html=True)
            return df
        else:
            st.markdown(f'<div class="custom-box">❌ DATA FETCH FAILED - Status Code: {response.status_code}</div>', unsafe_allow_html=True)
            return None
    except Exception as e:
        st.markdown(f'<div class="custom-box">❌ ERROR FETCHING DATA: {e}</div>', unsafe_allow_html=True)
        return None
launch_data = fetch_spacex_data()

# ---- DATA PREPROCESSING ----
def clean_launch_data(df):
    if df is None or df.empty:
        st.markdown('<div class="custom-box">❌ No data to process.</div>', unsafe_allow_html=True)
        return None
    
    key_columns = ["name", "date_utc", "success", "rocket", "launchpad"]
    df = df[key_columns].copy()
    
    df["date_utc"] = pd.to_datetime(df["date_utc"], errors="coerce")
    df["year"] = df["date_utc"].dt.year.astype(int)

    df["success"] = df["success"].fillna(False).astype(bool)
    df["rocket"] = df["rocket"].astype(str)
    df["launchpad"] = df["launchpad"].astype(str)
    
    st.markdown('<div class="custom-box">✓ DATA PROCESSED: Ready for analysis.</div>', unsafe_allow_html=True)
    return df

if launch_data is not None:
    launch_data = clean_launch_data(launch_data)
    if launch_data is not None:
        
        # ---- DATABASE STORAGE ----
        def save_to_db(df, db_name="spacex_data.db"):
            try:
                conn = sqlite3.connect(db_name)
                df.to_sql("launches", conn, if_exists="replace", index=False)
                conn.close()
                st.markdown(f'<div class="custom-box">✓ DATA SAVED: Stored in {db_name}</div>', unsafe_allow_html=True)
            except sqlite3.Error as e:
                st.markdown(f'<div class="custom-box">❌ DATABASE ERROR: {e}</div>', unsafe_allow_html=True)
        save_to_db(launch_data)

    
        # ---- DATA PREVIEW ----
        st.markdown('<h5>📋 Launch Records:</h5>', unsafe_allow_html=True)
        num_rows = st.slider("Select number of rows to display:", 5, 205, 20)
        st.dataframe(launch_data.head(num_rows), use_container_width=True)

        # ---- INTERACTIVE VISUALIZATIONS ----
        st.markdown("<h5>📊 Mission Insights:</h5>", unsafe_allow_html=True)
        st.write("**Choose Visualization:**")
        viz_type = st.selectbox("", 
                        ["Success Rate by Year", "Launches by Year", "Success by Rocket","Success/Failure Distribution", "Launch Timeline"], 
                        key="select_viz")

        if viz_type == "Success Rate by Year":
            success_trend = launch_data.groupby("year")["success"].mean().reset_index()
            fig = px.bar(success_trend, x="year", y="success", title="Mission Success Trajectory",
                        labels={"success": "Success Rate", "year": "Year"},
                        color_discrete_sequence=["#0096FF"])
            fig.update_layout(
                plot_bgcolor="#000000",  
                paper_bgcolor="#000000", 
                font_color="#FFFFFF",
                title_font=dict(color="#FFFFFF"),
                xaxis=dict(title_font=dict(color="#FFFFFF")),
                yaxis=dict(title_font=dict(color="#FFFFFF"))
            )
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "Launches by Year":
            launch_counts = launch_data["year"].value_counts().sort_index().reset_index()
            launch_counts.columns = ["year", "count"]
            fig = px.bar(launch_counts, x="year", y="count", title="Launch Frequency",
                        labels={"count": "Number of Launches", "year": "Year"},
                        color_discrete_sequence=["#0096FF"]) 
            fig.update_layout(
                plot_bgcolor="#000000",
                paper_bgcolor="#000000",
                font_color="#FFFFFF",
                title_font=dict(color="#FFFFFF"),
                xaxis=dict(title_font=dict(color="#FFFFFF")),
                yaxis=dict(title_font=dict(color="#FFFFFF"))
            )
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "Success by Rocket":
            rocket_success = launch_data.groupby("rocket")["success"].mean().reset_index()
            fig = px.bar(rocket_success, x="rocket", y="success", title="Success Rate by Rocket",
                        labels={"success": "Success Rate", "rocket": "Rocket ID"},
                        color_discrete_sequence=["#0096FF"]) 
            fig.update_layout(
                plot_bgcolor="#000000",
                paper_bgcolor="#000000",
                font_color="#FFFFFF",
                title_font=dict(color="#FFFFFF"),
                xaxis=dict(title_font=dict(color="#FFFFFF")),
                yaxis=dict(title_font=dict(color="#FFFFFF"))
                )
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Success/Failure Distribution":
            success_counts = launch_data["success"].value_counts().reset_index()
            success_counts.columns = ["success", "count"]
            success_counts["success"] = success_counts["success"].map({True: "Success", False: "Failure"})
            fig = px.pie(success_counts, values="count", names="success", 
                        title="Mission Success vs. Failure",
                        color_discrete_sequence=["#0096FF", "#FF4500"])  
            fig.update_layout(
                plot_bgcolor="#000000",
                paper_bgcolor="#000000",
                font_color="#FFFFFF",
                title_font=dict(color="#FFFFFF"),
                legend=dict(font=dict(color="#FFFFFF"))
                )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Launch Timeline":
            fig = px.scatter(launch_data, x="date_utc", y="success", 
                            title="Launch Timeline",
                            labels={"date_utc": "Date", "success": "Outcome"},
                            color="success", 
                            color_discrete_map={True: "#FF4500", False: "#0096FF"})  
            fig.update_layout(
                plot_bgcolor="#000000",
                paper_bgcolor="#000000",
                font_color="#FFFFFF",
                title_font=dict(color="#FFFFFF"),
                xaxis=dict(title_font=dict(color="#FFFFFF")),
                yaxis=dict(title_font=dict(color="#FFFFFF"), 
                        tickvals=[0, 1], 
                        ticktext=["Failure", "Success"])
            )
            fig.update_traces(marker=dict(size=10))  
            st.plotly_chart(fig, use_container_width=True)
        

        

        

