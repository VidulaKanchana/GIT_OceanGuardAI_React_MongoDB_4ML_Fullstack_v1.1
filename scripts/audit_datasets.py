import os
import json
import pandas as pd
import numpy as np

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Datasets")

def audit_file(filename):
    filepath = os.path.join(DATASET_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": f"File {filename} not found at {filepath}"}
    
    df = pd.read_csv(filepath)
    info = {
        "filename": filename,
        "rows": len(df),
        "columns_count": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": {col: int(df[col].isnull().sum()) for col in df.columns if df[col].isnull().sum() > 0},
        "numeric_summary": {},
        "categorical_summary": {}
    }

    for col in df.select_dtypes(include=[np.number]).columns:
        info["numeric_summary"][col] = {
            "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
            "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
            "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
            "std": float(df[col].std()) if not pd.isna(df[col].std()) else None
        }

    for col in df.select_dtypes(include=['object', 'category']).columns:
        val_counts = df[col].value_counts().head(10).to_dict()
        info["categorical_summary"][col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": {str(k): int(v) for k, v in val_counts.items()}
        }
        
    return info, df

def main():
    print("=== OCEAN GUARD AI: COMPREHENSIVE DATASET AUDIT ===")
    os.makedirs("docs", exist_ok=True)
    
    files = ["c1_trips.csv", "c2_zone_days.csv", "c3_market_prices.csv", "c4_fuel_scenarios.csv"]
    reports = {}
    dfs = {}
    
    for f in files:
        print(f"\n--- Auditing {f} ---")
        info, df = audit_file(f)
        reports[f] = info
        dfs[f] = df
        print(f"Rows: {info['rows']}, Columns: {info['columns_count']}")
        print(f"Columns: {info['columns']}")
        if info['null_counts']:
            print(f"Nulls found: {info['null_counts']}")
        else:
            print("No missing values detected.")
            
    # Check Cross-component key linkages
    print("\n=== CROSS-COMPONENT INTEGRATION AUDIT ===")
    df_c1 = dfs.get("c1_trips.csv")
    df_c2 = dfs.get("c2_zone_days.csv")
    df_c3 = dfs.get("c3_market_prices.csv")
    df_c4 = dfs.get("c4_fuel_scenarios.csv")
    
    cross_info = {}
    
    # C1 and C4 linkage: c1_trip_id vs trip_id
    if df_c1 is not None and df_c4 is not None:
        c1_ids = set(df_c1["trip_id"])
        c4_c1_ids = set(df_c4["c1_trip_id"])
        overlap_c1_c4 = c1_ids.intersection(c4_c1_ids)
        print(f"C1 trip_id count: {len(c1_ids)}")
        print(f"C4 c1_trip_id count: {len(c4_c1_ids)}")
        print(f"Intersection of C1 trips in C4: {len(overlap_c1_c4)} / {len(c1_ids)}")
        cross_info["c1_c4_link"] = {
            "c1_trips": len(c1_ids),
            "c4_trips": len(c4_c1_ids),
            "overlap": len(overlap_c1_c4)
        }
        
    # C1 and C2 zone linkages
    if df_c1 is not None and df_c2 is not None:
        c1_zones = set(df_c1["zone_id"])
        c2_zones = set(df_c2["zone_id"])
        c2_c1_nearest = set(df_c2["c1_nearest_centroid_id"].dropna())
        print(f"C1 zones: {c1_zones}")
        print(f"C2 zone count: {len(c2_zones)}")
        print(f"C2 references to C1 zones: {c2_c1_nearest}")
        cross_info["zones"] = {
            "c1_zones": list(c1_zones),
            "c2_zone_count": len(c2_zones),
            "c2_referenced_c1_zones": list(c2_c1_nearest)
        }
        
    # C4 references to C2
    if df_c4 is not None:
        c4_c2_zones = set(df_c4["c2_spatial_nearest_zone_id"].dropna())
        print(f"C4 unique c2_spatial_nearest_zone_id count: {len(c4_c2_zones)}")
        cross_info["c4_c2_zones"] = {
            "unique_referenced": len(c4_c2_zones),
            "zone_link_scopes": df_c4["zone_link_scope"].value_counts().to_dict()
        }
        
    # C3 Markets and Ports
    if df_c3 is not None:
        print(f"C3 Markets: {df_c3['market_id'].unique()}")
        print(f"C3 Species: {df_c3['species_id'].unique()}")
        print(f"C3 Date range: {df_c3['date'].min()} to {df_c3['date'].max()}")
        cross_info["c3_market_info"] = {
            "markets": list(df_c3['market_id'].unique()),
            "ports": list(df_c3['market_port_id'].unique()),
            "species": list(df_c3['species_id'].unique()),
            "date_range": [str(df_c3['date'].min()), str(df_c3['date'].max())]
        }
        
    # Save raw audit summary to JSON for markdown doc generation
    audit_results = {
        "files": reports,
        "cross_linkages": cross_info
    }
    
    with open(os.path.join("docs", "audit_raw_results.json"), "w") as f:
        json.dump(audit_results, f, indent=2)
        
    print("\nAudit completed and saved to docs/audit_raw_results.json")

if __name__ == "__main__":
    main()
