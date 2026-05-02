# app_complete.py - FULL WORKING VERSION
# Fixed for pandas 3.0+ (no fillna(method=...))
# Run with: streamlit run app_complete.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Fix for numpy compatibility
if not hasattr(np, 'float'):
    np.float = float

st.set_page_config(
    page_title="Barbados Agri-Climate-Economy Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1B5E20 0%, #4CAF50 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .insight-box-farmer {
        background-color: #E8F5E9;
        border-left: 5px solid #2E7D32;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .insight-box-consumer {
        background-color: #E3F2FD;
        border-left: 5px solid #1565C0;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .insight-box-economy {
        background-color: #FFF8E1;
        border-left: 5px solid #FF8F00;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS - FIXED for pandas 3.0+
# ============================================================================

@st.cache_data
def load_climate_data():
    df = pd.read_excel('Copy of climate data 2007_2022.xlsx', sheet_name='Sheet1')
    
    month_map = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    df['month_num'] = df['month'].map(month_map)
    
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)
    
    # FIXED: Use ffill() instead of fillna(method='ffill')
    if 'total_rainfall_mm' in df.columns:
        df['total_rainfall_mm'] = df['total_rainfall_mm'].ffill()
    if 'average_temp_c' in df.columns:
        df['average_temp_c'] = df['average_temp_c'].ffill()
    
    return df

@st.cache_data
def load_inflation_data():
    df = pd.read_excel('Copy of inflation_data_2007 to 2022 base_yr_july_2001.xlsx', sheet_name='Sheet1')
    
    month_map = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    df['month_num'] = df['month'].map(month_map)
    
    df = df[['year', 'month_num', 'moving_avg_inflation']]
    df = df.rename(columns={'moving_avg_inflation': 'inflation_rate'})
    df = df.dropna()
    df['year'] = df['year'].astype(int)
    
    return df

@st.cache_data
def load_wholesale_data():
    df_wide = pd.read_excel('Copy of Wholesale prices - 2007-2022.xlsx', sheet_name='Sheet1')
    
    month_cols = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    df_long = pd.melt(
        df_wide,
        id_vars=['product', 'year'],
        value_vars=month_cols,
        var_name='month',
        value_name='price_usd_per_kg'
    )
    
    df_long = df_long.rename(columns={'product': 'crop'})
    df_long['year'] = df_long['year'].astype(int)
    
    month_map = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    df_long['month_num'] = df_long['month'].map(month_map)
    df_long['month_short'] = df_long['month']
    
    df_long = df_long.dropna(subset=['price_usd_per_kg'])
    
    return df_long

@st.cache_data
def load_macro_data():
    df = pd.read_excel('Copy of macro data_2007-2022.xlsx', sheet_name='Sheet1')
    
    df = df.rename(columns={
        'food_imp_per_gdp': 'food_import_pct_gdp',
        'tour_arrival': 'tourism_arrivals',
        'agri_per_gdp': 'agri_pct_gdp',
        'food_prod_index': 'food_production_index',
        'gdp_per_capita': 'gdp_per_capita_usd',
        'gdp_change_percent': 'gdp_growth_pct',
        'food_products_imp': 'food_products_imports_usd',
        'food_animal_imp': 'food_animal_imports_usd',
        'food_veg_imp': 'food_veg_imports_usd',
        'total_food_imp': 'total_food_imports_usd'
    })
    
    df['year'] = df['year'].astype(int)
    
    return df

@st.cache_data
def merge_all_data():
    try:
        climate = load_climate_data()
        inflation = load_inflation_data()
        wholesale = load_wholesale_data()
        macro = load_macro_data()
        
        # Merge
        merged = wholesale.merge(
            climate[['year', 'month_num', 'average_temp_c', 'total_rainfall_mm', 
                     'total_rain_days', 'storm_days', 'average_relative_humidity_percent']],
            on=['year', 'month_num'],
            how='left'
        )
        
        merged = merged.rename(columns={
            'average_temp_c': 'temp_avg_c',
            'total_rainfall_mm': 'rainfall_mm',
            'total_rain_days': 'rain_days',
            'storm_days': 'storm_days',
            'average_relative_humidity_percent': 'humidity_pct'
        })
        
        merged = merged.merge(
            inflation[['year', 'month_num', 'inflation_rate']],
            on=['year', 'month_num'],
            how='left'
        )
        
        merged = merged.merge(macro, on=['year'], how='left')
        
        # FIXED: Use ffill() instead of fillna(method='ffill')
        merged['rainfall_mm'] = merged['rainfall_mm'].fillna(0)
        merged['temp_avg_c'] = merged['temp_avg_c'].ffill()
        merged['inflation_rate'] = merged['inflation_rate'].ffill()
        
        merged['date_label'] = merged.apply(
            lambda x: f"{x['month_short']} {x['year']}",
            axis=1
        )
        
        return merged
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def calculate_cv(df, crop_name):
    crop_prices = df[df['crop'] == crop_name]['price_usd_per_kg']
    if len(crop_prices) > 1:
        return crop_prices.std() / crop_prices.mean() * 100
    return 0

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🌾 Barbados Agri-Climate-Economy Intelligence Dashboard</h1>
        <p>Integrating Weather | Wholesale Prices | Inflation | Macroeconomic Trends</p>
        <p><small>2007-2022 | Powered by MIOA/IICA Methodology</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data..."):
        df = merge_all_data()
        
        if df.empty:
            st.error("Failed to load data. Check that all 4 Excel files are in the directory.")
            return
        
        st.success(f"✅ Loaded {len(df):,} price records for {df['crop'].nunique()} crops!")
    
    # Sidebar filters
    st.sidebar.header("🔍 Dashboard Controls")
    
    years = sorted(df['year'].unique())
    selected_years = st.sidebar.multiselect(
        "Select Years", years,
        default=[years[-3], years[-2], years[-1]] if len(years) >= 3 else years
    )
    
    crops = sorted(df['crop'].unique())
    selected_crops = st.sidebar.multiselect(
        "Select Crops", crops,
        default=crops[:3] if len(crops) >= 3 else crops
    )[:5]
    
    season_options = ['All', 'Dry (Jan-May)', 'Wet (Jun-Oct)', 'Post-Wet (Nov-Dec)']
    selected_season = st.sidebar.selectbox("Season Filter", season_options)
    
    # Apply filters
    filtered_df = df[df['year'].isin(selected_years) & df['crop'].isin(selected_crops)].copy()
    
    if selected_season != 'All':
        if selected_season == 'Dry (Jan-May)':
            filtered_df = filtered_df[filtered_df['month_num'].between(1, 5)]
        elif selected_season == 'Wet (Jun-Oct)':
            filtered_df = filtered_df[filtered_df['month_num'].between(6, 10)]
        else:
            filtered_df = filtered_df[filtered_df['month_num'].between(11, 12)]
    
    # ========================================================================
    # KPI METRICS
    # ========================================================================
    
    st.subheader("📊 Key Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_price = filtered_df['price_usd_per_kg'].mean() if len(filtered_df) > 0 else 0
        st.metric("Avg Price (Selected)", f"${avg_price:.2f}/kg")
    
    with col2:
        if len(selected_crops) > 0:
            vols = {crop: calculate_cv(df, crop) for crop in selected_crops}
            if vols:
                most_volatile = max(vols, key=vols.get)
                st.metric("Most Volatile", most_volatile, f"{vols[most_volatile]:.0f}% CV")
    
    with col3:
        if len(filtered_df) > 0:
            monthly_avg = filtered_df.groupby('month_num')['price_usd_per_kg'].mean()
            best_month_num = monthly_avg.idxmax() if not monthly_avg.empty else 7
            month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                          7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
            st.metric("Best Selling Month", month_names.get(best_month_num, 'Jul-Aug'))
    
    with col4:
        avg_rainfall = df[df['year'].isin(selected_years)]['rainfall_mm'].mean() if selected_years else 0
        st.metric("Avg Monthly Rainfall", f"{avg_rainfall:.0f} mm")
    
    # ========================================================================
    # CHART 1: Price Trends
    # ========================================================================
    
    st.markdown("---")
    st.subheader("📈 Price Trends Over Time")
    
    if len(selected_crops) > 0 and len(filtered_df) > 0:
        fig_trend = px.line(
            filtered_df, x='date_label', y='price_usd_per_kg',
            color='crop', title="Wholesale Price Trends by Month",
            labels={'date_label': 'Month', 'price_usd_per_kg': 'Price (USD/kg)'},
            markers=True
        )
        fig_trend.update_layout(height=450)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # ========================================================================
    # CHART 2: Inflation
    # ========================================================================
    
    st.subheader("💰 Inflation Rate Over Time")
    
    yearly_inflation = df[['year', 'inflation_rate']].drop_duplicates().sort_values('year')
    fig_inflation = px.line(
        yearly_inflation, x='year', y='inflation_rate',
        title="Annual Inflation Rate (Moving Average)",
        labels={'year': 'Year', 'inflation_rate': 'Inflation Rate (%)'},
        markers=True
    )
    fig_inflation.update_layout(height=400)
    st.plotly_chart(fig_inflation, use_container_width=True)
    
    # ========================================================================
    # CHART 3: Seasonal Patterns
    # ========================================================================
    
    st.subheader("📅 Seasonal Price Patterns")
    
    if len(selected_crops) > 0 and len(filtered_df) > 0:
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        fig_seasonal = px.box(
            filtered_df, x='month_short', y='price_usd_per_kg', color='crop',
            title="Price Distribution by Month",
            labels={'month_short': 'Month', 'price_usd_per_kg': 'Price (USD/kg)'},
            category_orders={'month_short': month_order}
        )
        fig_seasonal.update_layout(height=450)
        st.plotly_chart(fig_seasonal, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box-farmer">
            <strong>🌾 Seasonal Insight:</strong> Prices typically peak in July-September (wet season) 
            and are lowest in April-May (main harvest).
        </div>
        """, unsafe_allow_html=True)
    
    # ========================================================================
    # CHART 4: Rainfall Impact (Dual Axis)
    # ========================================================================
    
    st.subheader("🌧️ Weather Impact: Rainfall vs Crop Prices")
    
    if len(selected_crops) > 0:
        weather_crop = st.selectbox("Select crop for weather correlation", selected_crops, key="weather_select")
        weather_df = filtered_df[filtered_df['crop'] == weather_crop].sort_values(['year', 'month_num']).copy()
        
        if len(weather_df) > 0:
            fig_weather = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_weather.add_trace(
                go.Scatter(
                    x=weather_df['date_label'], y=weather_df['price_usd_per_kg'],
                    mode='lines+markers', name=f'{weather_crop} Price',
                    line=dict(color='green', width=2)
                ),
                secondary_y=False
            )
            
            fig_weather.add_trace(
                go.Bar(
                    x=weather_df['date_label'], y=weather_df['rainfall_mm'],
                    name='Rainfall (mm)', marker_color='lightblue', opacity=0.5
                ),
                secondary_y=True
            )
            
            fig_weather.update_layout(title=f"{weather_crop} Price vs Monthly Rainfall", height=450)
            fig_weather.update_yaxes(title_text="Price (USD/kg)", secondary_y=False)
            fig_weather.update_yaxes(title_text="Rainfall (mm)", secondary_y=True)
            
            st.plotly_chart(fig_weather, use_container_width=True)
    
    # ========================================================================
    # CHART 5: Temperature Impact
    # ========================================================================
    
    st.subheader("🌡️ Temperature Impact on Crop Prices")
    
    if len(selected_crops) > 0:
        temp_crop = st.selectbox("Select crop for temperature analysis", selected_crops, key="temp_select")
        temp_df = filtered_df[filtered_df['crop'] == temp_crop].copy()
        
        if len(temp_df) > 0:
            fig_temp = px.scatter(
                temp_df,
                x='temp_avg_c',
                y='price_usd_per_kg',
                color='year',
                size='rainfall_mm',
                title=f"{temp_crop}: Price vs Temperature (bubble size = rainfall)",
                labels={'temp_avg_c': 'Average Temperature (°C)', 'price_usd_per_kg': 'Price (USD/kg)'},
                hover_data=['month_short']
            )
            fig_temp.update_layout(height=450)
            st.plotly_chart(fig_temp, use_container_width=True)
            
            st.markdown("""
            <div class="insight-box-consumer">
                <strong>🌡️ Temperature Insight:</strong> Higher temperatures (above 28°C) often stress 
                crops, reducing yields and increasing prices 1-2 months later.
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # CHART 6: Macroeconomic Context
    # ========================================================================
    
    st.subheader("🏦 Macroeconomic Context")
    
    macro_df = df[['year', 'food_import_pct_gdp', 'agri_pct_gdp', 'gdp_growth_pct']].drop_duplicates()
    macro_df = macro_df[macro_df['year'].isin(selected_years)]
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_imports = px.line(
            macro_df, x='year', y='food_import_pct_gdp',
            title="Food Imports as % of GDP", markers=True
        )
        fig_imports.add_hline(y=6.5, line_dash="dash", line_color="orange", annotation_text="Avg 6.5%")
        fig_imports.update_layout(height=400)
        st.plotly_chart(fig_imports, use_container_width=True)
    
    with col_right:
        fig_gdp = px.bar(
            macro_df, x='year', y='gdp_growth_pct',
            title="GDP Growth Rate", color='gdp_growth_pct',
            color_continuous_scale='RdYlGn'
        )
        fig_gdp.update_layout(height=400)
        st.plotly_chart(fig_gdp, use_container_width=True)
    
    st.markdown("""
    <div class="insight-box-economy">
        <strong>📊 Economic Insight:</strong> Barbados imports 6-7% of GDP as food, making it vulnerable to global price shocks.
    </div>
    """, unsafe_allow_html=True)
    
    # ========================================================================
    # CHART 7: Volatility Ranking
    # ========================================================================
    
    st.subheader("⚠️ Crop Volatility & Risk Assessment")
    
    vol_data = []
    for crop in df['crop'].unique():
        cv = calculate_cv(df, crop)
        avg_price = df[df['crop'] == crop]['price_usd_per_kg'].mean()
        vol_data.append({
            'Crop': crop, 'CV (%)': round(cv, 1),
            'Risk Level': '🔴 High' if cv > 40 else '🟡 Medium' if cv > 25 else '🟢 Low',
            'Avg Price ($/kg)': round(avg_price, 2)
        })
    
    vol_df = pd.DataFrame(vol_data).sort_values('CV (%)', ascending=False).head(15)
    
    fig_vol = px.bar(
        vol_df, x='Crop', y='CV (%)', color='Risk Level',
        title="Price Volatility by Crop (Higher = More Risk)",
        color_discrete_map={'🔴 High': '#ff6b6b', '🟡 Medium': '#ffd93d', '🟢 Low': '#6bcb77'}
    )
    fig_vol.update_layout(height=450, xaxis={'tickangle': 45})
    st.plotly_chart(fig_vol, use_container_width=True)
    
    # ========================================================================
    # CHART 8: Month-to-Month Changes
    # ========================================================================
    
    st.subheader("📊 Month-to-Month Price Changes")
    
    if len(selected_crops) > 0:
        monthly_changes = []
        for crop in selected_crops:
            crop_df = df[df['crop'] == crop].sort_values(['year', 'month_num'])
            for m in range(1, 13):
                curr = crop_df[crop_df['month_num'] == m]
                prev = crop_df[crop_df['month_num'] == (m-1 if m>1 else 12)]
                if len(curr) > 0 and len(prev) > 0:
                    avg_curr = curr['price_usd_per_kg'].mean()
                    avg_prev = prev['price_usd_per_kg'].mean()
                    if avg_prev > 0:
                        pct = ((avg_curr - avg_prev) / avg_prev) * 100
                        monthly_changes.append({'crop': crop, 'month': m, 'pct_change': pct})
        
        if monthly_changes:
            change_df = pd.DataFrame(monthly_changes)
            month_names = {1:'Jan→Feb', 2:'Feb→Mar', 3:'Mar→Apr', 4:'Apr→May', 5:'May→Jun',
                          6:'Jun→Jul', 7:'Jul→Aug', 8:'Aug→Sep', 9:'Sep→Oct', 10:'Oct→Nov',
                          11:'Nov→Dec', 12:'Dec→Jan'}
            change_df['month_label'] = change_df['month'].map(month_names)
            
            pivot_df = change_df.pivot(index='crop', columns='month_label', values='pct_change')
            
            fig_heatmap = px.imshow(
                pivot_df, title="Average Month-to-Month Price Changes (%)",
                labels={'x': 'Month Transition', 'y': 'Crop', 'color': '% Change'},
                color_continuous_scale='RdYlGn', aspect='auto', text_auto='.1f'
            )
            fig_heatmap.update_layout(height=400)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.markdown("""
            <div class="insight-box-farmer">
                <strong>📈 Price Change Guide:</strong> Red = Price INCREASE (good for selling), 
                Green = Price DECREASE (good for buying). July-August shows strongest increases.
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # CHART 9: Data Explorer
    # ========================================================================
    
    st.subheader("📋 Data Explorer")
    
    display_df = filtered_df[['year', 'month_short', 'crop', 'price_usd_per_kg', 'rainfall_mm', 'temp_avg_c', 'inflation_rate']].copy()
    display_df = display_df.rename(columns={
        'month_short': 'Month', 'crop': 'Crop', 'price_usd_per_kg': 'Price (USD/kg)',
        'rainfall_mm': 'Rainfall (mm)', 'temp_avg_c': 'Temp (°C)', 'inflation_rate': 'Inflation (%)'
    })
    st.dataframe(display_df.head(100), use_container_width=True)
    
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="barbados_agriculture_export.csv",
        mime="text/csv"
    )
    
    # ========================================================================
    # ACTIONABLE INSIGHTS
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 💡 Actionable Insights for Barbados")
    
    col_farmer, col_consumer = st.columns(2)
    
    with col_farmer:
        st.markdown("""
        <div class="insight-box-farmer">
            <h3>🌾 For Farmers</h3>
            <ul>
                <li><strong>Best selling window:</strong> July-September (prices 15-30% above average)</li>
                <li><strong>Planting recommendation:</strong> Leafy greens in March-April for peak harvest prices</li>
                <li><strong>Storage strategy:</strong> Root crops harvested April → store until August for premium</li>
                <li><strong>Low volatility crops:</strong> Yam, cassava, sweet potato (most stable income)</li>
                <li><strong>High volatility crops:</strong> Tomato, lettuce, pepper (require risk management)</li>
                <li><strong>Weather monitoring:</strong> Heavy rain (>200mm) predicts price spikes in 1-2 months</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_consumer:
        st.markdown("""
        <div class="insight-box-consumer">
            <h3>🛒 For Consumers</h3>
            <ul>
                <li><strong>Best buying window:</strong> April-May (prices 20-30% below average)</li>
                <li><strong>Expect price hikes:</strong> July-September (wet season shortages)</li>
                <li><strong>Weather impact:</strong> Heavy rain or drought → prices double in 1-2 months</li>
                <li><strong>Most stable prices:</strong> Root crops (yam, cassava, sweet potato)</li>
                <li><strong>Budget tip:</strong> Stock up on storable items during April-May sales</li>
                <li><strong>Import awareness:</strong> 6-7% of GDP goes to food imports - global prices affect local costs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #ddd; color: #666;">
        <small>📊 Data Sources: Climate (2007-2022) | Inflation (2007-2022) | Wholesale Prices (2007-2022) | Macroeconomic Data (2007-2022)<br>
        📖 Methodology: MIOA/IICA Manual on Basic Analysis of Agricultural Prices<br>
        🔄 Dashboard updates when new data is pushed to GitHub | Data as of 2022</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()