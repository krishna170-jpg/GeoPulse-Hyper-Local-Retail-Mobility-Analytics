import osmnx as ox
import pandas as pd

print("Connecting to OpenStreetMap...")
print("Searching retail locations in Dibrugarh, Assam...")

place = "Dibrugarh, Assam, India"

tags = {
    "shop": True,
    "amenity": ["marketplace"]
}

try:
    retail = ox.features_from_place(
        place,
        tags=tags
    )
except Exception as error:
    print("Place boundary search failed:", error)
    print("Trying a 5 km search around Dibrugarh...")
    retail = ox.features_from_address(
        place,
        tags=tags,
        dist=5000
    )

if retail.empty:
    print("No retail records found in this query.")
    raise SystemExit(0)

retail = retail.reset_index()

retail["latitude"] = retail.geometry.representative_point().y
retail["longitude"] = retail.geometry.representative_point().x

columns = [
    "name",
    "shop",
    "amenity",
    "brand",
    "operator",
    "latitude",
    "longitude"
]

for column in columns:
    if column not in retail.columns:
        retail[column] = None

retail = retail[columns].drop_duplicates()

os.makedirs("data/raw", exist_ok=True)

retail.to_csv(
    "data/raw/dibrugarh_retail.csv",
    index=False
)

print("\nRetail data collection successful!")
print("Total mapped records:", len(retail))
print("Saved: data/raw/dibrugarh_retail.csv")

print("\nFirst five records:")
print(retail.head())
