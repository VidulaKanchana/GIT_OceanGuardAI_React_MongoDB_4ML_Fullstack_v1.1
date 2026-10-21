import os
import sys
import pandas as pd
from datetime import datetime

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.connection import get_database
from app.db.indexes import create_indexes
from app.core.logging import logger

def seed():
    logger.info("=== Starting Idempotent Database Seeding ===")
    db = get_database()
    create_indexes(db)
    
    # 1. Seed Default Users
    logger.info("Seeding default role-based users...")
    users = [
        {
            "user_id": "U001",
            "email": "admin@oceanguard.ai",
            "full_name": "Dr. Nishantha Silva (Admin)",
            "hashed_password": get_password_hash("AdminPass123!"),
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "user_id": "U002",
            "email": "researcher@oceanguard.ai",
            "full_name": "Kavinda Perera (Fisheries Researcher)",
            "hashed_password": get_password_hash("ResearchPass123!"),
            "role": "researcher",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "user_id": "U003",
            "email": "fisherman@oceanguard.ai",
            "full_name": "Sunil Fernando (Artisanal Skipper)",
            "hashed_password": get_password_hash("FishermanPass123!"),
            "role": "fisherman",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    for u in users:
        db.users.update_one({"email": u["email"]}, {"$set": u}, upsert=True)
    logger.info(f"Seeded {len(users)} default users.")

    # 2. Seed Reference Fishing Ports
    logger.info("Seeding Sri Lankan reference fishing ports...")
    ports = [
        {"port_id": "P_GALLE", "name": "Galle Fishery Harbour", "latitude": 6.033, "longitude": 80.217, "province": "Southern", "district": "Galle"},
        {"port_id": "P_MIRISSA", "name": "Mirissa Fishery Harbour", "latitude": 5.945, "longitude": 80.455, "province": "Southern", "district": "Matara"},
        {"port_id": "P_TANGALLE", "name": "Tangalle Fishery Harbour", "latitude": 6.024, "longitude": 80.796, "province": "Southern", "district": "Hambantota"},
        {"port_id": "P_NEGOMBO", "name": "Negombo Fishery Harbour", "latitude": 7.208, "longitude": 79.835, "province": "Western", "district": "Gampaha"},
        {"port_id": "P_PELIYAGODA", "name": "Peliyagoda Central Market Port", "latitude": 6.965, "longitude": 79.885, "province": "Western", "district": "Colombo"},
        {"port_id": "P_BERUWALA", "name": "Beruwala Fishery Harbour", "latitude": 6.478, "longitude": 79.982, "province": "Western", "district": "Kalutara"},
        {"port_id": "P_TRINCOMALEE", "name": "Cod Bay Trincomalee", "latitude": 8.571, "longitude": 81.233, "province": "Eastern", "district": "Trincomalee"}
    ]
    for p in ports:
        db.fishing_ports.update_one({"port_id": p["port_id"]}, {"$set": p}, upsert=True)
    logger.info(f"Seeded {len(ports)} reference fishing ports.")

    # 3. Seed Reference Fish Species
    logger.info("Seeding reference fish species with biological & perishability parameters...")
    species_list = [
        {
            "species_id": "SP_YELLOWFIN",
            "name": "Yellowfin tuna",
            "scientific_name": "Thunnus albacares",
            "optimal_temp_c": 28.0,
            "temp_tolerance_sd": 2.2,
            "perishability_base_hours_at_0c": 120.0,
            "q10_decay_factor": 2.2,
            "high_value": True
        },
        {
            "species_id": "SP_SKIPJACK",
            "name": "Skipjack tuna",
            "scientific_name": "Katsuwonus pelamis",
            "optimal_temp_c": 27.5,
            "temp_tolerance_sd": 2.5,
            "perishability_base_hours_at_0c": 96.0,
            "q10_decay_factor": 2.4,
            "high_value": False
        },
        {
            "species_id": "SP_MACKEREL",
            "name": "Indian mackerel",
            "scientific_name": "Rastrelliger kanagurta",
            "optimal_temp_c": 28.5,
            "temp_tolerance_sd": 2.0,
            "perishability_base_hours_at_0c": 72.0,
            "q10_decay_factor": 2.5,
            "high_value": False
        },
        {
            "species_id": "SP_SARDINE",
            "name": "Sardine",
            "scientific_name": "Sardinella longiceps",
            "optimal_temp_c": 27.0,
            "temp_tolerance_sd": 2.0,
            "perishability_base_hours_at_0c": 48.0,
            "q10_decay_factor": 2.8,
            "high_value": False
        },
        {
            "species_id": "SP_SEER",
            "name": "Seer fish / King mackerel",
            "scientific_name": "Scomberomorus commerson",
            "optimal_temp_c": 28.2,
            "temp_tolerance_sd": 2.1,
            "perishability_base_hours_at_0c": 110.0,
            "q10_decay_factor": 2.1,
            "high_value": True
        }
    ]
    for s in species_list:
        db.fish_species.update_one({"species_id": s["species_id"]}, {"$set": s}, upsert=True)
    logger.info(f"Seeded {len(species_list)} reference fish species.")

    # 4. Seed Vessels from C1 dataset
    c1_path = os.path.join(settings.DATASETS_DIR, "c1_trips.csv")
    if os.path.exists(c1_path):
        logger.info(f"Extracting unique vessels from {c1_path}...")
        df_c1 = pd.read_csv(c1_path)
        vessel_cols = ["vessel_id", "vessel_type", "vessel_length_m", "vessel_beam_m", "lightship_mass_kg", "assumed_payload_limit_kg", "assumed_lightship_freeboard_m"]
        df_vessels = df_c1[vessel_cols].drop_duplicates(subset=["vessel_id"])
        
        vessels_to_insert = []
        for _, row in df_vessels.iterrows():
            vessels_to_insert.append({
                "vessel_id": row["vessel_id"],
                "owner_id": "U003",
                "name": f"FV {row['vessel_type']}-{row['vessel_id']}",
                "vessel_type": row["vessel_type"],
                "length_m": float(row["vessel_length_m"]),
                "beam_m": float(row["vessel_beam_m"]),
                "lightship_mass_kg": float(row["lightship_mass_kg"]),
                "payload_limit_kg": float(row["assumed_payload_limit_kg"]),
                "lightship_freeboard_m": float(row["assumed_lightship_freeboard_m"]),
                "home_port_id": "P_GALLE" if row["vessel_type"] == "OFRP" else "P_MIRISSA",
                "provenance": "synthetic_design_not_measured",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            })
        for v in vessels_to_insert[:50]:  # Seed first 50 unique representative vessels
            db.vessels.update_one({"vessel_id": v["vessel_id"]}, {"$set": v}, upsert=True)
        logger.info(f"Seeded {min(50, len(vessels_to_insert))} representative vessels into db.vessels.")

    # 5. Seed C2 Spatial Zones
    c2_path = os.path.join(settings.DATASETS_DIR, "c2_zone_days.csv")
    if os.path.exists(c2_path):
        logger.info(f"Extracting spatial fishing zones from {c2_path}...")
        df_c2 = pd.read_csv(c2_path)
        zones_unique = df_c2[["zone_id", "zone_latitude_deg", "zone_longitude_deg", "c1_nearest_centroid_id"]].drop_duplicates(subset=["zone_id"])
        
        for _, z in zones_unique.iterrows():
            zone_doc = {
                "zone_id": z["zone_id"],
                "latitude": float(z["zone_latitude_deg"]),
                "longitude": float(z["zone_longitude_deg"]),
                "c1_nearest_centroid_id": z["c1_nearest_centroid_id"],
                "provenance": "SYNTHETIC_SPATIAL_GRID",
                "status": "active"
            }
            db.fishing_zones.update_one({"zone_id": z["zone_id"]}, {"$set": zone_doc}, upsert=True)
        logger.info(f"Seeded {len(zones_unique)} spatial fishing zones into db.fishing_zones.")

    # 6. Seed Sample Market Historical Prices (First 200 records for fast initial seeding)
    c3_path = os.path.join(settings.DATASETS_DIR, "c3_market_prices.csv")
    if os.path.exists(c3_path):
        logger.info(f"Seeding initial market price data from {c3_path}...")
        df_c3 = pd.read_csv(c3_path)
        for _, r in df_c3.head(250).iterrows():
            doc = {
                "record_id": r["record_id"],
                "date": str(r["date"]),
                "market_id": r["market_id"],
                "market_name": r["market_name"],
                "market_port_id": r["market_port_id"],
                "species_id": r["species_id"],
                "species_name": r["species_name"],
                "price_lkr_per_kg": float(r["price_lkr_per_kg"]),
                "supply_ratio_simulated": float(r["supply_ratio_simulated"]),
                "demand_index_simulated": float(r["demand_index_simulated"]),
                "provenance": "SYNTHETIC_SCENARIO_NOT_OBSERVED",
                "price_safety_status": "NOT_REAL_MARKET_QUOTE"
            }
            db.market_prices.update_one({"record_id": r["record_id"]}, {"$set": doc}, upsert=True)
        logger.info("Seeded initial market prices into db.market_prices.")

    logger.info("=== Database Seeding Complete & Verified ===")

if __name__ == "__main__":
    seed()
