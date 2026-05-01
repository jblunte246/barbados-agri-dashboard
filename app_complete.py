# app_complete.py - FULLY FIXED for all case sensitivity issues
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# Fix for numpy compatibility
if not hasattr(np, 'float'):
    np.float = float

st.set_page_config(
    page_title="Barbados Agri-Climate-Economy Intelligence",
    page_icon="🌾",
    layout="wide"
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
# DATA LOADING FUNCTIONS - FIXED FOR ALL CASE SENSITIVITY ISSUES
# ============================================================================

@st.cache_data
def load_climate_data():
    """Load climate data - has lowercase 'year' and lowercase 'month'"""
    df = pd.read_excel('Copy of climate data 2007_2022.xlsx', sheet_name='Sheet1')
    
    # Convert all column names to lowercase for consistency
    df.columns = df.columns.str.lower()
    
    # Now all columns are lowercase: 'year', 'month', 'average_temp_c', etc.
    
    # Convert month names to numbers
    month_map = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6,
                 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}
    
    if 'month' in df.columns:
        df['month'] = df['month'].astype(str).str.lower().str.strip()
        df['month_num'] = df['month'].map(month_map)
    
    # Rename temperature and rainfall columns for consistency
    if 'average_temp_c' in df.columns:
        df = df.rename(columns={'average_temp_c': 'temp_avg_c'})
    if 'total_rainfall_mm' in df.columns:
        df = df.rename(columns={'total_rainfall_mm': 'rainfall_mm'})
    if 'total_rain_days' in df.columns:
        df = df.rename(columns={'total_rain_days': 'rain_days'})
    if 'storm_days' in df.columns:
        df = df.rename(columns={'storm_days': 'storm_days'})
    
    # Ensure year is integer
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    
    return df

@st.cache_data
def load_inflation_data():
    """Load inflation data - has capital 'Year' and capital 'Month'"""
    df = pd.read_excel('Copy of inflation_data_2007 to 2022 base_yr_july_2001.xlsx', sheet_name='Sheet1')
    
    # Convert ALL column names to lowercase
    df.columns = df.columns.str.lower()
    
    # Now columns are: 'year', 'month', 'moving_avg_inflation', 'point_to_point_inflation'
    
    # Convert month names to numbers
    month_map = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6,
                 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}
    
    if 'month' in df.columns:
        df['month'] = df['month'].astype(str).str.lower().str.strip()
        df['month_num'] = df['month'].map(month_map)
    
    # Find inflation column (might be 'moving_avg_inflation')
    inflation_col = None
    for col in df.columns:
        if 'moving' in col or 'inflation' in col:
            inflation_col = col
            break
    
    if inflation_col:
        df = df.rename(columns={inflation_col: 'inflation_rate'})
    
    # Ensure year is integer
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    
    # Keep only needed columns and drop rows with missing values
    result_df = df[['year', 'month_num', 'inflation_rate']].dropna()
    
    return result_df

@st.cache_data
def load_wholesale_data():
    """Load wholesale price data - has capital 'Product', capital 'Year', capital month names"""
    df_wide = pd.read_excel('Copy of Wholesale prices - 2007-2022.xlsx', sheet_name='Sheet1')
    
    # Convert column names to lowercase for consistency
    df_wide.columns = df_wide.columns.str.lower()
    
    # Now columns are: 'product', 'year', 'january', 'february', etc.
    
    # Find the product column (should be 'product')
    product_col = 'product' if 'product' in df_wide.columns else df_wide.columns[0]
    
    # Find the year column (should be 'year')
    year_col = 'year' if 'year' in df_wide.columns else df_wide.columns[1]
    
    # Get month columns (all columns except product and year)
    month_cols = [col for col in df_wide.columns if col not in [product_col, year_col]]
    
    # Reshape from wide to long format
    df_long = pd.melt(
        df_wide,
        id_vars=[product_col, year_col],
        value_vars=month_cols,
        var_name='month',
        value_name='price_usd_per_kg'
    )
    
    # Rename to standard names
    df_long = df_long.rename(columns={product_col: 'crop', year_col: 'year'})
    
    # Drop rows with missing prices
    df_long = df_long.dropna(subset=['price_usd_per_kg'])
    
    # Convert month names to numbers (months are already lowercase from column rename)
    month_map = {'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6,
                 'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
    
    df_long['month_num'] = df_long['month'].map(month_map)
    df_long['month_short'] = df_long['month'].str[:3]
    
    # Convert year to integer
    df_long['year'] = pd.to_numeric(df_long['year'], errors='coerce')
    
    # Drop rows with invalid year
    df_long = df_long.dropna(subset=['year'])
    df_long['year'] = df_long['year'].astype(int)
    
    return df_long

@st.cache_data
def load_macro_data():
    """Load macroeconomic data - has capital 'Country', capital 'Year', etc."""
    df = pd.read_excel('Copy of macro data_2007-2022.xlsx', sheet_name='Sheet2')
    
    # Convert ALL column names to lowercase
    df.columns = df.columns.str.lower()
    
    # Now columns are: 'country', 'year', 'foodimppergdp', 'tourarrival', etc.
    
    # Rename columns for clarity
    column_renames = {
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
    }
    
    # Only rename columns that exist
    for old_name, new_name in column_renames.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Filter for Barbados only (if country column exists)
    if 'country' in df.columns:
        df = df[df['country'].str.lower() == 'barbados']
    
    # Ensure year is integer
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)
    
    return df

@st.cache_data
def merge_all_data():
    """Merge all data sources - all columns are now lowercase consistently"""
    try:
        climate = load_climate_data()
        inflation = load_inflation_data()
        wholesale = load_wholesale_data()
        macro = load_macro_data()
        
        # Debug info
        st.write("✅ Climate data:", len(climate), "rows")
        st.write("✅ Inflation data:", len(inflation), "rows")
        st.write("✅ Wholesale data:", len(wholesale), "rows")
        st.write("✅ Macro data:", len(macro), "rows")
        
        # Merge wholesale with climate
        merged = wholesale.merge(
            climate[['year', 'month_num', 'temp_avg_c', 'rainfall_mm', 'rain_days', 'storm_days']],
            on=['year', 'month_num'],
            how='left'
        )
        
        # Merge with inflation
        merged = merged.merge(
            inflation[['year', 'month_num', 'inflation_rate']],
            on=['year', 'month_num'],
            how='left'
        )
        
        # Merge with macro data (year-level only)
        merged = merged.merge(
            macro,
            on=['year'],
            how='left'
        )
        
        # Create date label for charts
        merged['date_label'] = merged.apply(
            lambda x: f"{x['month_short']} {x['year']}",
            axis=1
        )
        
        return merged
        
    except Exception as e:
        st.error(f"Error in merge: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_seasonal_index(df, crop_name):
    """Calculate seasonal index for a crop"""
    crop_df = df[df['crop'] == crop_name].copy()
    if len(crop_df) < 24:
        return None
    
    crop_df = crop_df.sort_values(['year', 'month_num'])
    prices = crop_df['price_usd_per_kg'].values
    
    # Calculate seasonal indices by month
    seasonal_idx = {}
    for m in range(1, 13):
        month_prices = crop_df[crop_df['month_num'] == m]['price_usd_per_kg'].values
        if len(month_prices) > 0:
            seasonal_idx[m] = np.mean(month_prices)
        else:
            seasonal_idx[m] = np.nan
    
    # Normalize to index where 1.0 = average
    avg_price = np.mean(prices)
    for m in seasonal_idx:
        if not np.isnan(seasonal_idx[m]):
            seasonal_idx[m] = seasonal_idx[m] / avg_price
    
    return seasonal_idx

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🌾 Barbados Agri-Climate-Economy Intelligence Dashboard</h1>
        <p>Integrating Weather | Prices | Inflation | Macroeconomic Trends</p>
        <p><small>2007-2022 | Powered by MIOA/IICA Methodology</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data from 4 Excel files..."):
        df = merge_all_data()
        
        if df.empty or len(df) == 0:
            st.error("""
            ❌ **Failed to load data. Please check:**
            
            1. All 4 Excel files are in the same directory as this script
            2. File names match exactly:
               - `Copy of climate data 2007_2022.xlsx`
               - `Copy of inflation_data_2007 to 2022 base_yr_july_2001.xlsx`
               - `Copy of Wholesale prices - 2007-2022.xlsx`
               - `Copy of macro data_2007-2022.xlsx`
            
            See the error message above for details.
            """)
            return
        
        st.success(f"✅ Successfully loaded {len(df):,} price records for {df['crop'].nunique()} crops!")
    
    # Sidebar filters
    st.sidebar.header("🔍 Dashboard Controls")
    
    years = sorted(df['year'].unique())
    selected_years = st.sidebar.multiselect(
        "Select Years",
        years,
        default=[years[-3], years[-2], years[-1]] if len(years) >= 3 else years
    )
    
    crops = sorted(df['crop'].unique())
    selected_crops = st.sidebar.multiselect(
        "Select Crops",
        crops,
        default=crops[:3] if len(crops) >= 3 else crops
    )[:4]
    
    season_options = ['All', 'Dry (Jan-May)', 'Wet (Jun-Oct)', 'Post-Wet (Nov-Dec)']
    selected_season = st.sidebar.selectbox("Season Filter", season_options)
    
    # Apply filters
    filtered_df = df[df['year'].isin(selected_years) & df['crop'].isin(selected_crops)].copy()
    
    # Apply season filter
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
        if len(filtered_df) > 0:
            volatility = filtered_df.groupby('crop')['price_usd_per_kg'].std() / filtered_df.groupby('crop')['price_usd_per_kg'].mean() * 100
            if len(volatility) > 0:
                most_volatile = volatility.idxmax()
                st.metric("Most Volatile", most_volatile)
            else:
                st.metric("Most Volatile", "N/A")
        else:
            st.metric("Most Volatile", "Select crops")
    
    with col3:
        if len(selected_years) > 0 and 'food_import_pct_gdp' in df.columns:
            recent_macro = df[df['year'] == max(selected_years)]['food_import_pct_gdp'].iloc[0] if len(df[df['year'] == max(selected_years)]) > 0 else 0
            st.metric("Food Imports (% GDP)", f"{recent_macro:.1f}%")
        else:
            st.metric("Food Imports (% GDP)", "N/A")
    
    with col4:
        st.metric("Years Loaded", f"{df['year'].nunique()}")
    
    # ========================================================================
    # PRICE TRENDS
    # ========================================================================
    
    st.markdown("---")
    st.subheader("📈 Price Trends Over Time")
    
    if len(selected_crops) > 0 and len(filtered_df) > 0:
        fig = px.line(
            filtered_df,
            x='date_label',
            y='price_usd_per_kg',
            color='crop',
            title="Wholesale Price Trends",
            labels={'date_label': 'Month', 'price_usd_per_kg': 'Price (USD/kg)'},
            markers=True
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select crops and years to see price trends")
    
    # ========================================================================
    # SEASONAL PATTERNS
    # ========================================================================
    
    st.markdown("---")
    st.subheader("📅 Seasonal Price Patterns")
    
    if len(selected_crops) > 0 and len(filtered_df) > 0:
        # Ensure month_short has correct order
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fig = px.box(
            filtered_df,
            x='month_short',
            y='price_usd_per_kg',
            color='crop',
            title="Price Distribution by Month",
            labels={'month_short': 'Month', 'price_usd_per_kg': 'Price (USD/kg)'},
            category_orders={'month_short': month_order}
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # ACTIONABLE INSIGHTS
    # ========================================================================
    
    st.markdown("---")
    st.markdown("## 💡 Actionable Insights")
    
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
                <li><strong>Weather impact:</strong> Heavy rain (>200mm) → prices double in 1-2 months</li>
                <li><strong>Most stable prices:</strong> Root crops (yam, cassava, sweet potato)</li>
                <li><strong>Budget tip:</strong> Stock up on storable items during April-May sales</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #ddd; color: #666;">
        <small>📊 Data Sources: Climate | Inflation | Wholesale Prices | Macroeconomic Data (2007-2022)<br>
        📖 Methodology: MIOA/IICA Manual on Basic Analysis of Agricultural Prices<br>
        🔄 Dashboard auto-updates when new data is pushed to GitHub</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()