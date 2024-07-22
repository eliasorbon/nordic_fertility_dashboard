# Fertility Rate Dashboard

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import seaborn as sns
import io
import requests

# Set up the color palette and style
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    print("Seaborn whitegrid style not found. Using default style.")
    plt.style.use('default')

color_palette = ['#4C566A', '#5E81AC', '#88C0D0', '#8FBCBB', '#81A1C1']
sns.set_palette(color_palette)

# Custom fonts (ensure these fonts are installed on your system or use default ones)
title_font = fm.FontProperties(family='Arial', weight='bold', size=16)
label_font = fm.FontProperties(family='Arial', size=12)
tick_font = fm.FontProperties(family='Arial', size=10)

def get_country_codes(countries):
    url = "http://api.worldbank.org/v2/country"
    params = {"format": "json", "per_page": 300}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        country_dict = {item['name'].lower(): item['id'] for item in data[1]}
        
        codes = []
        for country in countries:
            code = country_dict.get(country.lower())
            if code:
                codes.append(code)
            else:
                print(f"Warning: Could not find code for {country}. Using name as is.")
                codes.append(country)
        
        return codes
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching country codes: {e}")
        return countries

def fetch_world_bank_data(countries, indicator="SP.DYN.TFRT.IN", start_year=1960, end_year=2022, timeout=30):
    base_url = "http://api.worldbank.org/v2/country/{}/indicator/{}"
    
    all_data = []
    
    for country in countries:
        url = base_url.format(country, indicator)
        params = {
            "date": f"{start_year}:{end_year}",
            "format": "json",
            "per_page": 1000
        }
        
        try:
            print(f"Fetching data for {country}...")
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if len(data) > 1:
                country_data = [(item['country']['value'], item['date'], item['value']) for item in data[1]]
                all_data.extend(country_data)
            else:
                print(f"No data available for {country}")
            
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching data for {country}: {e}")
    
    if not all_data:
        print("No data was fetched from the World Bank API.")
        return None
    
    print("Processing fetched data...")
    df = pd.DataFrame(all_data, columns=['Country', 'Year', 'Fertility Rate'])
    df['Fertility Rate'] = pd.to_numeric(df['Fertility Rate'], errors='coerce')
    df = df.pivot(index='Year', columns='Country', values='Fertility Rate').reset_index()
    df['Year'] = pd.to_numeric(df['Year'])
    
    return df

def create_dashboard(countries, data=None):
    if data is None or data.empty:
        print("No data available. Please check your internet connection and try again.")
        return None
    
    fig = Figure(figsize=(16, 10), dpi=300)
    canvas = FigureCanvas(fig)
    
    # Set background color
    fig.patch.set_facecolor('#ECEFF4')
    
    # Main title
    fig.suptitle('Nordic Countries Fertility Rate Analysis', fontproperties=title_font, fontsize=24, y=0.95, color='#2E3440')

    # Adjust subplot parameters to give specified padding
    fig.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.85, wspace=0.3)
    
    # Fertility Rate Trends
    ax1 = fig.add_subplot(121)
    for i, country in enumerate(countries):
        if country in data.columns:
            ax1.plot(data['Year'], data[country], label=country, linewidth=2.5, color=color_palette[i % len(color_palette)])
        else:
            print(f"Warning: No data available for {country}")
    ax1.set_title('Fertility Rate Trends (1960-2022)', fontproperties=title_font, pad=20, color='#2E3440')
    ax1.set_xlabel('Year', fontproperties=label_font, color='#4C566A')
    ax1.set_ylabel('Fertility Rate (births per woman)', fontproperties=label_font, color='#4C566A')
    ax1.tick_params(axis='both', which='major', labelsize=10, colors='#4C566A')
    ax1.legend(prop=label_font, loc='upper left', bbox_to_anchor=(1, 1), borderaxespad=0.)
    ax1.grid(True, linestyle='--', alpha=0.7, color='#D8DEE9')
    ax1.set_facecolor('#E5E9F0')
    
    # Latest Fertility Rates
    ax2 = fig.add_subplot(122)
    latest_year = data['Year'].max()
    latest_data = data[data['Year'] == latest_year].melt(id_vars=['Year'], var_name='Country', value_name='Fertility Rate')
    latest_data = latest_data.sort_values('Fertility Rate', ascending=True)
    bars = ax2.barh(latest_data['Country'], latest_data['Fertility Rate'], color=color_palette)
    ax2.set_title(f'Fertility Rates ({latest_year})', fontproperties=title_font, pad=20, color='#2E3440')
    ax2.set_xlabel('Fertility Rate (births per woman)', fontproperties=label_font, color='#4C566A')
    ax2.tick_params(axis='both', which='major', labelsize=10, colors='#4C566A')
    ax2.set_facecolor('#E5E9F0')
    
    # Add value labels on end of each bar
    for bar in bars:
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}',
                 ha='left', va='center', fontproperties=tick_font, color='#2E3440')
    
    # Improve layout
    fig.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])
    
    # Add a footnote
    fig.text(0.05, 0.02, 'Data source: World Bank', fontproperties=tick_font, color='#4C566A')
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    
    return buf

# Example usage:
nordic_countries = ['Norway', 'Sweden', 'Denmark', 'Finland', 'Iceland']
print("Fetching country codes...")
country_codes = get_country_codes(nordic_countries)
print("Fetching data from World Bank...")
data = fetch_world_bank_data(country_codes)
dashboard_image = create_dashboard(nordic_countries, data)

if dashboard_image:
    # To save the dashboard as an image file:
    with open('nordic_fertility_dashboard.png', 'wb') as f:
        f.write(dashboard_image.getvalue())
    print("Dashboard saved as 'nordic_fertility_dashboard.png'")
else:
    print("Failed to create dashboard due to data retrieval issues.")

# If you're using this in a Jupyter notebook, you can display the image directly:
# from IPython.display import Image
# Image(dashboard_image.getvalue())
