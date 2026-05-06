
import sys
import pandas as pd
from backend.data_loader import get_country_commerce_profile, load_commerce_data

try:
    print("Loading data...")
    df = load_commerce_data()
    print(f"Data loaded. Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    print("\nChecking DZA...")
    dza_rows = df[df['Code_ISO'] == 'DZA']
    print(f"Rows matching DZA: {len(dza_rows)}")
    
    if len(dza_rows) > 0:
        print("DZA Row content:")
        print(dza_rows.iloc[0])
        
    print("\nCalling get_country_commerce_profile('DZA')...")
    profile = get_country_commerce_profile('DZA')
    if profile:
        print("Profile found!")
        print(profile.get('world_bank_data'))
    else:
        print("Profile NOT found.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
