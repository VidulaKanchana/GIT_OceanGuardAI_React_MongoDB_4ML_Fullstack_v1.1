import pymongo
from app.core.logging import logger

def create_indexes(db):
    try:
        # Users
        db.users.create_index([("email", pymongo.ASCENDING)], unique=True)
        db.users.create_index([("role", pymongo.ASCENDING)])
        
        # Vessels
        db.vessels.create_index([("vessel_id", pymongo.ASCENDING)], unique=True)
        db.vessels.create_index([("owner_id", pymongo.ASCENDING)])
        
        # Trips
        db.trips.create_index([("trip_id", pymongo.ASCENDING)], unique=True)
        db.trips.create_index([("vessel_id", pymongo.ASCENDING)])
        db.trips.create_index([("status", pymongo.ASCENDING)])
        
        # C1 Safety Assessments
        db.safety_assessments.create_index([("assessment_id", pymongo.ASCENDING)], unique=True)
        db.safety_assessments.create_index([("trip_id", pymongo.ASCENDING)])
        db.safety_assessments.create_index([("vessel_id", pymongo.ASCENDING)])
        
        # C2 Fishing Recommendations
        db.fishing_recommendations.create_index([("recommendation_id", pymongo.ASCENDING)], unique=True)
        db.fishing_recommendations.create_index([("zone_id", pymongo.ASCENDING)])
        
        # C3 Market Forecasts & Recommendations
        db.market_recommendations.create_index([("recommendation_id", pymongo.ASCENDING)], unique=True)
        db.market_prices.create_index([("record_id", pymongo.ASCENDING)], unique=True)
        db.market_prices.create_index([("market_id", pymongo.ASCENDING), ("species_id", pymongo.ASCENDING), ("date", pymongo.ASCENDING)])
        
        # C4 Fuel Predictions
        db.fuel_predictions.create_index([("prediction_id", pymongo.ASCENDING)], unique=True)
        db.fuel_predictions.create_index([("trip_id", pymongo.ASCENDING)])
        
        # Observations
        db.observations.create_index([("observation_id", pymongo.ASCENDING)], unique=True)
        db.observations.create_index([("type", pymongo.ASCENDING)])
        db.observations.create_index([("verification_status", pymongo.ASCENDING)])
        
        # Rescue / Emergency Events
        db.rescue_events.create_index([("event_id", pymongo.ASCENDING)], unique=True)
        db.rescue_events.create_index([("vessel_id", pymongo.ASCENDING)])
        db.rescue_events.create_index([("status", pymongo.ASCENDING)])
        
        # Model Registry
        db.model_versions.create_index([("component", pymongo.ASCENDING), ("version", pymongo.ASCENDING)], unique=True)
        db.training_jobs.create_index([("job_id", pymongo.ASCENDING)], unique=True)

        logger.info("MongoDB database indexes successfully applied.")
    except Exception as e:
        logger.warning(f"Note on index application: {e}")
