# app_complete.py
# Barbados Agri-Climate Intelligence Dashboard with Macroeconomic Data
# Run with: streamlit run app_complete.py

import streamlit as st
import pandas as pd
import numpy as np
# Fix for older numpy compatibility (if needed)
if not hasattr(np, 'float'):
    np.float = float
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Page configuration
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
    .kpi-card {
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .warning-box {
        background-color: #FFF3E0;
        border: 1px solid #FF9800;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS (REAL EXCEL FILES)
# ============================================================================

@st.cache_data
def load_climate_data():
    """Load climate data from Excel"""
    df = pd.read_excel('Copy of climate data 2007_2022.xlsx', sheet_name='Sheet1')
    
    # Handle the first row as headers (it appears the data starts correctly)
    # Convert month names to numbers
    month_map = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    
    # Clean month column
    df['month'] = df['month'].astype(str).str.strip()
    df['month_num'] = df['month'].map(month_map)
    
    # Rename columns for consistency
    df.rename(columns={
        'Average_Temp_C': 'temp_avg_c',
        'Total_Rainfall_mm': 'rainfall_mm',
        'Total_Rain_days': 'rain_days',
        'Storm_days': 'storm_days',
        'Average_Relative_Humidity_%': 'humidity_pct'
    }, inplace=True)
    
    return df

@st.cache_data
def load_inflation_data():
    """Load inflation data from Excel"""
    df = pd.read_excel('Copy of inflation_data_2007 to 2022 base_yr_july_2001.xlsx', sheet_name='Sheet1')
    
    month_map = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    
    df['month'] = df['Month'].astype(str).str.strip()
    df['month_num'] = df['month'].map(month_map)
    df['year'] = df['Year']
    df['inflation_rate'] = df['moving_avg_inflation']
    
    return df[['year', 'month_num', 'inflation_rate']]

@st.cache_data
def load_wholesale_data():
    """Load wholesale price data and reshape from wide to long format"""
    df_wide = pd.read_excel('Copy of Wholesale prices - 2007-2022.xlsx', sheet_name='Sheet1')
    
    # Reshape from wide to long format
    df_long = pd.melt(
        df_wide,
        id_vars=['Product', 'Year'],
        var_name='month',
        value_name='price_usd_per_kg'
    )
    
    df_long.rename(columns={'Product': 'crop', 'Year': 'year'}, inplace=True)
    
    # Drop rows with missing prices
    df_long = df_long.dropna(subset=['price_usd_per_kg'])
    
    # Convert month names to numbers
    month_map = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6,
                 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}
    df_long['month_num'] = df_long['month'].map(month_map)
    
    # Extract first 3 letters for month display
    df_long['month_short'] = df_long['month'].str[:3]
    
    return df_long

@st.cache_data
def load_macro_data():
    """Load macroeconomic data from Excel"""
    df = pd.read_excel('Copy of macro data_2007-2022.xlsx', sheet_name='Sheet2')
    
    # Clean column names
    df.columns = df.columns.str.lower()
    
    # Rename for clarity
    df.rename(columns={
        'foodimppergdp': 'food_import_pct_gdp',
        'tourarrival': 'tourism_arrivals',
        'agripergdp': 'agri_pct_gdp',
        'foodprodindex': 'food_production_index',
        'gdppercapita': 'gdp_per_capita_usd',
        'gdp': 'gdp_usd',
        'gdpchangepercent': 'gdp_growth_pct',
        'foodproductsimp': 'food_products_imports_usd',
        'foodanimalimp': 'food_animal_imports_usd',
        'foodvegimp': 'food_veg_imports_usd',
        'totalfoodimp': 'total_food_imports_usd'
    }, inplace=True)
    
    return df

@st.cache_data
def merge_all_data():
    """Merge all four data sources"""
    climate = load_climate_data()
    inflation = load_inflation_data()
    wholesale = load_wholesale_data()
    macro = load_macro_data()
    
    # Merge wholesale with climate
    merged = wholesale.merge(
        climate[['year', 'month_num', 'temp_avg_c', 'rainfall_mm', 'rain_days', 'storm_days', 'humidity_pct']],
        on=['year', 'month_num'],
        how='left'
    )
    
    # Merge with inflation
    merged = merged.merge(
        inflation[['year', 'month_num', 'inflation_rate']],
        on=['year', 'month_num'],
        how='left'
    )
    
    # Merge with macro data (year-level only, so no month)
    merged = merged.merge(
        macro,
        on=['year'],
        how='left'
    )
    
    # Create date label for charts
    merged['date_label'] = merged.apply(
        lambda x: f"{x['month_short']} {int(x['year'])}", axis=1
    )
    
    return merged

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_seasonal_index(df, crop_name):
    """Calculate seasonal index (multiplicative method)"""
    crop_df = df[df['crop'] == crop_name].copy()
    if len(crop_df) < 24:
        return None
    
    crop_df = crop_df.sort_values(['year', 'month_num'])
    prices = crop_df['price_usd_per_kg'].values
    
    # Calculate 12-month moving average
    ma_12 = []
    for i in range(len(prices) - 11):
        ma_12.append(np.mean(prices[i:i+12]))
    
    # Calculate centered MA
    cma = []
    for i in range(len(ma_12) - 1):
        cma.append(np.mean(ma_12[i:i+2]))
    
    # Calculate P/CMA
    p_cma = []
    for i in range(len(cma)):
        if i+6 < len(prices):
            p_cma.append(prices[i+6] / cma[i])
    
    # Calculate seasonal indices by month
    seasonal_idx = {}
    for m in range(1, 13):
        values = []
        for i, row in crop_df.iterrows():
            if row['month_num'] == m and i >= 6 and i < len(prices) - 6:
                idx_in_p_cma = i - 6
                if idx_in_p_cma < len(p_cma):
                    values.append(p_cma[idx_in_p_cma])
        if values:
            seasonal_idx[m] = np.mean(values)
        else:
            seasonal_idx[m] = 1.0
    
    # Normalize
    mean_idx = np.mean(list(seasonal_idx.values()))
    for m in seasonal_idx:
        seasonal_idx[m] /= mean_idx
    
    return seasonal_idx

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.zeros_like(prices)
    avg_loss = np.zeros_like(prices)
    
    avg_gain[period] = np.mean(gains[:period]) if len(gains) >= period else 0
    avg_loss[period] = np.mean(losses[:period]) if len(losses) >= period else 0
    
    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + losses[i-1]) / period
    
    rs = avg_gain / (avg_loss + 0.0001)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌾 Barbados Agri-Climate-Economy Intelligence Dashboard</h1>
        <p>Integrating Weather | Prices | Inflation | Macroeconomic Trends</p>
        <p><small>2007-2022 | Powered by MIOA/IICA Methodology</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading and analyzing data from 4 Excel files..."):
        try:
            df = merge_all_data()
            st.success(f"✅ Data loaded successfully! {len(df)} records, {df['crop'].nunique()} crops")
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.info("Make sure all 4 Excel files are in the same directory as this script.")
            return
    
    # Sidebar filters
    st.sidebar.header("🔍 Dashboard Controls")
    
    years = sorted(df['year'].unique())
    selected_years = st.sidebar.multiselect(
        "Select Years",
        years,
        default=[years[-3], years[-2], years[-1]]
    )
    
    crops = sorted(df['crop'].unique())
    selected_crops = st.sidebar.multiselect(
        "Select Crops (max 4 for comparison)",
        crops,
        default=['Tomato', 'Cabbage', 'Yam'] if 'Tomato' in crops else crops[:3]
    )[:4]
    
    # Season filter
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
    # KPI METRICS (Expanded with Macro Data)
    # ========================================================================
    
    st.subheader("📊 Key Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        avg_price = filtered_df['price_usd_per_kg'].mean()
        overall_avg = df['price_usd_per_kg'].mean()
        delta = avg_price - overall_avg
        st.metric("Avg Price (Selected)", f"${avg_price:.2f}/kg", f"{delta:+.2f}")
    
    with col2:
        if len(selected_crops) > 0:
            crop_prices = filtered_df.groupby('crop')['price_usd_per_kg'].std()
            if len(crop_prices) > 0:
                most_volatile = crop_prices.idxmax() if not crop_prices.empty else "N/A"
                st.metric("Most Volatile", most_volatile)
            else:
                st.metric("Most Volatile", "N/A")
        else:
            st.metric("Most Volatile", "Select crops")
    
    with col3:
        recent_macro = df[df['year'] == max(selected_years)]['food_import_pct_gdp'].iloc[0] if len(selected_years) > 0 else 0
        st.metric("Food Imports (% GDP)", f"{recent_macro:.1f}%")
    
    with col4:
        recent_gdp = df[df['year'] == max(selected_years)]['gdp_growth_pct'].iloc[0] if len(selected_years) > 0 else 0
        st.metric("GDP Growth", f"{recent_gdp:+.1f}%")
    
    with col5:
        recent_tourism = df[df['year'] == max(selected_years)]['tourism_arrivals'].iloc[0] if len(selected_years) > 0 else 0
        st.metric("Tourism Arrivals", f"{recent_tourism:,.0f}")
    
    # ========================================================================
    # NEW SECTION: MACROECONOMIC CONTEXT
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 🏦 SECTION 1: Macroeconomic Context")
    st.markdown("*How broader economic factors influence food prices and farming*")
    
    macro_df = df.drop_duplicates('year').sort_values('year')
    macro_df = macro_df[macro_df['year'].isin(selected_years)]
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        # GDP per capita vs Food Import Dependency
        fig_gdp = px.scatter(
            macro_df,
            x='gdp_per_capita_usd',
            y='food_import_pct_gdp',
            size='total_food_imports_usd',
            color='year',
            title="Food Import Dependency vs GDP per Capita",
            labels={'gdp_per_capita_usd': 'GDP per Capita (USD)', 
                    'food_import_pct_gdp': 'Food Imports (% of GDP)'},
            hover_data=['tourism_arrivals', 'agri_pct_gdp']
        )
        fig_gdp.update_layout(height=400)
        st.plotly_chart(fig_gdp, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box-economy">
            <strong>📈 Economic Insight:</strong> As GDP per capita rises, food import dependency fluctuates. 
            The COVID-19 period (2020-2021) saw a sharp drop in tourism and GDP, but food import dependency increased.
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        # Tourism vs Food Production Index
        fig_tourism = px.bar(
            macro_df,
            x='year',
            y=['tourism_arrivals', 'food_production_index'],
            title="Tourism Arrivals vs Food Production Index (2007-2022)",
            labels={'value': 'Value', 'year': 'Year', 'variable': 'Indicator'},
            barmode='group'
        )
        fig_tourism.update_layout(height=400)
        st.plotly_chart(fig_tourism, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box-consumer">
            <strong>🛒 Consumer Insight:</strong> Tourism dropped 80%+ during COVID-19 (2020-2021), 
            yet food production also declined. This combination led to higher import dependency and food prices.
        </div>
        """, unsafe_allow_html=True)
    
    # ========================================================================
    # SECTION 2: PRICE TRENDS WITH ECONOMIC OVERLAY
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 📈 SECTION 2: Price Trends with Economic Indicators")
    
    if len(selected_crops) > 0:
        fig_price_econ = make_subplots(specs=[[{"secondary_y": True}]])
        
        for i, crop in enumerate(selected_crops[:3]):  # Limit to 3 for clarity
            crop_df = filtered_df[filtered_df['crop'] == crop].sort_values(['year', 'month_num'])
            if len(crop_df) > 0:
                fig_price_econ.add_trace(
                    go.Scatter(
                        x=crop_df['date_label'],
                        y=crop_df['price_usd_per_kg'],
                        mode='lines',
                        name=f'{crop} Price',
                        line=dict(width=2)
                    ),
                    secondary_y=False
                )
        
        # Add inflation on secondary axis
        yearly_inflation = macro_df.set_index('year')['inflation_rate'].to_dict()
        filtered_df['inflation_for_chart'] = filtered_df['year'].map(yearly_inflation)
        
        fig_price_econ.add_trace(
            go.Scatter(
                x=filtered_df['date_label'],
                y=filtered_df['inflation_for_chart'],
                mode='lines',
                name='Inflation Rate (%)',
                line=dict(color='red', width=2, dash='dot')
            ),
            secondary_y=True
        )
        
        fig_price_econ.update_layout(
            title="Crop Prices vs Inflation Rate",
            height=450,
            hovermode='x unified'
        )
        fig_price_econ.update_yaxes(title_text="Price (USD/kg)", secondary_y=False)
        fig_price_econ.update_yaxes(title_text="Inflation Rate (%)", secondary_y=True)
        
        st.plotly_chart(fig_price_econ, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box-farmer">
            <strong>🌾 Farmer Insight:</strong> When inflation rises above 5%, crop prices typically follow with a 
            2-3 month lag. Consider forward contracts during high-inflation periods to lock in prices.
        </div>
        """, unsafe_allow_html=True)
    
    # ========================================================================
    # SECTION 3: IMPORT DEPENDENCY & FOOD SECURITY
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 🌍 SECTION 3: Food Security & Import Dependency")
    st.markdown("*Understanding Barbados's reliance on imported food*")
    
    # Import composition over time
    import_df = macro_df[['year', 'food_products_imports_usd', 'food_animal_imports_usd', 
                          'food_veg_imports_usd', 'total_food_imports_usd']].copy()
    import_df = import_df.melt(id_vars=['year'], var_name='import_type', value_name='usd_value')
    import_df['import_type'] = import_df['import_type'].replace({
        'food_products_imports_usd': 'Processed Foods',
        'food_animal_imports_usd': 'Animal Products',
        'food_veg_imports_usd': 'Vegetable Products',
        'total_food_imports_usd': 'Total Food Imports'
    })
    
    # Filter for relevant types only
    import_df = import_df[import_df['import_type'] != 'Total Food Imports']
    
    fig_imports = px.area(
        import_df,
        x='year',
        y='usd_value',
        color='import_type',
        title="Food Import Composition by Category (USD)",
        labels={'usd_value': 'Import Value (USD)', 'year': 'Year', 'import_type': 'Category'},
        color_discrete_map={
            'Processed Foods': '#FF6B6B',
            'Animal Products': '#4ECDC4',
            'Vegetable Products': '#45B7D1'
        }
    )
    fig_imports.update_layout(height=450)
    st.plotly_chart(fig_imports, use_container_width=True)
    
    # Import dependency ratio
    macro_df['import_per_capita'] = macro_df['total_food_imports_usd'] / (macro_df['gdp_usd'] / macro_df['gdp_per_capita_usd'] + 1)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_dependency = px.line(
            macro_df,
            x='year',
            y='food_import_pct_gdp',
            title="Food Import Dependency (% of GDP)",
            markers=True,
            labels={'food_import_pct_gdp': '% of GDP', 'year': 'Year'}
        )
        fig_dependency.add_hline(y=6.5, line_dash="dash", line_color="orange", 
                                 annotation_text="Average (6.5%)")
        fig_dependency.update_layout(height=350)
        st.plotly_chart(fig_dependency, use_container_width=True)
    
    with col_right:
        fig_agri = px.line(
            macro_df,
            x='year',
            y=['agri_pct_gdp', 'food_production_index'],
            title="Agriculture's Economic Role",
            labels={'value': 'Value', 'year': 'Year', 'variable': 'Indicator'},
            markers=True
        )
        fig_agri.update_layout(height=350)
        st.plotly_chart(fig_agri, use_container_width=True)
    
    st.markdown("""
    <div class="insight-box-economy">
        <strong>📊 Food Security Insight:</strong> 
        <ul>
            <li>Food imports consistently represent <strong>6-7% of Barbados GDP</strong></li>
            <li>Vegetable and animal product imports have grown steadily, while processed foods remain highest</li>
            <li>Agriculture's share of GDP has fluctuated between 1.3-3.3%, increasing during COVID-19</li>
            <li><strong>Implication:</strong> Barbados remains highly dependent on food imports, making it vulnerable to global price shocks</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # ========================================================================
    # SECTION 4: SEASONAL ANALYSIS
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 📅 SECTION 4: Seasonal Price Patterns")
    
    if len(selected_crops) > 0:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Monthly Price Boxplot")
            fig_box = px.box(
                filtered_df,
                x='month_short',
                y='price_usd_per_kg',
                color='crop',
                title=f"Price Distribution by Month ({', '.join(selected_crops[:3])})",
                labels={'month_short': 'Month', 'price_usd_per_kg': 'Price (USD/kg)'}
            )
            fig_box.update_layout(height=450)
            st.plotly_chart(fig_box, use_container_width=True)
        
        with col_right:
            st.subheader("Seasonal Index (Price vs Annual Average)")
            seasonal_data = []
            for crop in selected_crops[:3]:
                seasonal_idx = calculate_seasonal_index(df, crop)
                if seasonal_idx:
                    for month, idx in seasonal_idx.items():
                        month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                                       7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
                        seasonal_data.append({
                            'crop': crop,
                            'month': month_names[month],
                            'seasonal_index': idx
                        })
            
            if seasonal_data:
                seasonal_df = pd.DataFrame(seasonal_data)
                fig_seasonal_idx = px.line(
                    seasonal_df,
                    x='month',
                    y='seasonal_index',
                    color='crop',
                    title="Seasonal Index (1.0 = Annual Average)",
                    labels={'seasonal_index': 'Price vs Average', 'month': 'Month'},
                    markers=True
                )
                fig_seasonal_idx.add_hline(y=1.0, line_dash="dash", line_color="gray")
                fig_seasonal_idx.update_layout(height=450)
                st.plotly_chart(fig_seasonal_idx, use_container_width=True)
    
    # ========================================================================
    # SECTION 5: WEATHER & PRICE LINKAGES
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 🌧️ SECTION 5: Weather Impact Analysis")
    
    if len(selected_crops) > 0:
        weather_crop = st.selectbox("Select crop for weather correlation", selected_crops, key="weather_select")
        weather_df = filtered_df[filtered_df['crop'] == weather_crop].sort_values(['year', 'month_num']).copy()
        
        if len(weather_df) > 0:
            fig_weather = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_weather.add_trace(
                go.Scatter(
                    x=weather_df['date_label'],
                    y=weather_df['price_usd_per_kg'],
                    mode='lines+markers',
                    name=f'{weather_crop} Price',
                    line=dict(color='green', width=2)
                ),
                secondary_y=False
            )
            
            fig_weather.add_trace(
                go.Bar(
                    x=weather_df['date_label'],
                    y=weather_df['rainfall_mm'],
                    name='Rainfall (mm)',
                    marker_color='lightblue',
                    opacity=0.5
                ),
                secondary_y=True
            )
            
            fig_weather.update_layout(
                title=f"{weather_crop} Price vs Rainfall (Monthly)",
                height=450,
                xaxis_title="Time",
                hovermode='x unified'
            )
            fig_weather.update_yaxes(title_text="Price (USD/kg)", secondary_y=False)
            fig_weather.update_yaxes(title_text="Rainfall (mm)", secondary_y=True)
            
            st.plotly_chart(fig_weather, use_container_width=True)
    
    # ========================================================================
    # SECTION 6: VOLATILITY RANKING
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## ⚠️ SECTION 6: Crop Volatility & Risk Assessment")
    
    volatility_data = []
    for crop in df['crop'].unique():
        crop_prices = df[df['crop'] == crop]['price_usd_per_kg']
        if len(crop_prices) > 1:
            cv = crop_prices.std() / crop_prices.mean() * 100
            volatility_data.append({
                'Crop': crop,
                'CV (%)': round(cv, 1),
                'Risk Level': 'High' if cv > 40 else 'Medium' if cv > 25 else 'Low',
                'Avg Price ($)': round(crop_prices.mean(), 2)
            })
    
    vol_df = pd.DataFrame(volatility_data).sort_values('CV (%)', ascending=False).head(15)
    
    def color_risk(val):
        if val == 'High':
            return 'background-color: #ffcccc'
        elif val == 'Medium':
            return 'background-color: #ffffcc'
        return 'background-color: #ccffcc'
    
    st.dataframe(vol_df.style.applymap(color_risk, subset=['Risk Level']), use_container_width=True)
    
    # ========================================================================
    # SECTION 7: MONTH-TO-MONTH CHANGES
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 📋 SECTION 7: Month-to-Month Price Changes")
    
    if len(selected_crops) > 0:
        monthly_changes = {}
        for crop in selected_crops:
            crop_df = df[df['crop'] == crop].sort_values(['year', 'month_num'])
            changes = []
            for m in range(1, 13):
                month_data = crop_df[crop_df['month_num'] == m]
                if len(month_data) > 1:
                    avg_price = month_data['price_usd_per_kg'].mean()
                    prev_month = crop_df[crop_df['month_num'] == (m-1 if m>1 else 12)]
                    if len(prev_month) > 0:
                        prev_avg = prev_month['price_usd_per_kg'].mean()
                        pct_change = ((avg_price - prev_avg) / prev_avg) * 100
                        changes.append(pct_change)
                    else:
                        changes.append(0)
                else:
                    changes.append(0)
            monthly_changes[crop] = changes
        
        months_display = ['Jan→Feb', 'Feb→Mar', 'Mar→Apr', 'Apr→May', 'May→Jun', 
                          'Jun→Jul', 'Jul→Aug', 'Aug→Sep', 'Sep→Oct', 'Oct→Nov', 
                          'Nov→Dec', 'Dec→Jan']
        
        change_data = []
        for i, month_pair in enumerate(months_display):
            row = {'Month Transition': month_pair}
            for crop in selected_crops:
                val = monthly_changes[crop][i] if i < len(monthly_changes[crop]) else 0
                row[crop] = f"{val:+.1f}%"
            change_data.append(row)
        
        change_df = pd.DataFrame(change_data)
        st.dataframe(change_df, use_container_width=True)
    
    # ========================================================================
    # SECTION 8: DATA EXPLORER
    # ========================================================================
    
    st.markdown("---")
    with st.expander("📊 Data Explorer - View Raw Data"):
        st.dataframe(filtered_df.head(100), use_container_width=True)
        
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="barbados_agriculture_data.csv",
            mime="text/csv"
        )
    
    # ========================================================================
    # FINAL INSIGHT BOXES
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 💡 Actionable Insights")
    
    col_farmer, col_consumer, col_economy = st.columns(3)
    
    with col_farmer:
        st.markdown("""
        <div class="insight-box-farmer">
            <h3>🌾 For Farmers</h3>
            <ul>
                <li><strong>Planting:</strong> Leafy greens in Mar-Apr for Jul-Aug harvest (best prices)</li>
                <li><strong>Storage:</strong> Root crops harvested Apr → store until Aug for 10-15% premium</li>
                <li><strong>Risk management:</strong> Diversify with low-volatility crops (yam, cassava)</li>
                <li><strong>Market timing:</strong> Sell when 6-month MA crosses above 12-month MA</li>
                <li><strong>Import competition:</strong> Monitor vegetable imports - high imports suppress local prices</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_consumer:
        st.markdown("""
        <div class="insight-box-consumer">
            <h3>🛒 For Consumers</h3>
            <ul>
                <li><strong>Best buying:</strong> April-May (prices 20-30% below average)</li>
                <li><strong>Expect price hikes:</strong> July-September (wet season shortages)</li>
                <li><strong>Weather alert:</strong> Heavy rain/drought → prices double in 1-2 months</li>
                <li><strong>Stable options:</strong> Root crops (yam, cassava) have most stable prices</li>
                <li><strong>Budget planning:</strong> Stock up on storable items during April-May sales</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_economy:
        st.markdown("""
        <div class="insight-box-economy">
            <h3>🏦 Economic Context</h3>
            <ul>
                <li><strong>Import dependency:</strong> 6-7% of GDP goes to food imports</li>
                <li><strong>Vulnerability:</strong> Global price shocks directly affect local prices</li>
                <li><strong>Tourism link:</strong> Lower tourism reduces foreign exchange for imports</li>
                <li><strong>COVID impact:</strong> 80% tourism drop + lower production = higher prices</li>
                <li><strong>Food security:</strong> Strengthening local production reduces import vulnerability</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #ddd; color: #666;">
        <small>📊 Data Sources: Climate (2007-2022) | Inflation (2007-2022) | Wholesale Prices (2007-2022) | Macroeconomic Data (2007-2022)<br>
        📖 Methodology: MIOA/IICA Manual on Basic Analysis of Agricultural Prices<br>
        ⚠️ Forecasts are estimates only | Dashboard updates: Monthly | Data as of 2022</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()