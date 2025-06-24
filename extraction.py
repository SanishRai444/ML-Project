import ee
import geemap
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta, timezone
import os

ee.Initialize(project='ff-sanishrai444')

def get_lat_lon(location_name):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(location_name)
    if not location:
        raise ValueError(f"Location '{location_name}' not found.")
    return location.latitude, location.longitude

def get_mean_image(collection_id, band_name, start_date, end_date, geometry):
    collection = ee.ImageCollection(collection_id).select(band_name).filterDate(start_date, end_date).filterBounds(geometry)
    count = collection.size().getInfo()
    if count == 0:
        return None
    mean_image = collection.mean().clip(geometry)
    return mean_image

def export_image(image, location_name, pollutant_name, date_str, region, scale,file_path):
    filename = f"{pollutant_name}_{location_name.replace(' ', '_')}_{date_str}.tif"
    output_path = os.path.join(file_path, filename)
    geemap.ee_export_image(
        image,
        filename=output_path,
        region=region.getInfo()['coordinates'],  # Rectangle coordinates
        scale=scale,
        crs='EPSG:4326'
    )
    return output_path

def extract_pollution_data(location_name,filepath):
    lat, lon = get_lat_lon(location_name)

    # Create 7x7 km rectangle (3.5 km buffer each side)
    buffer_m = 3500
    buffer_deg = buffer_m / 111320
    scale = 875  # 875 meters per pixel (~8x8 pixels for 7x7 km)

    region = ee.Geometry.Rectangle([
        [lon - buffer_deg, lat - buffer_deg],
        [lon + buffer_deg, lat + buffer_deg]
    ])
  
    now_utc = datetime.now(timezone.utc).date()
    today_str = now_utc.strftime('%Y-%m-%d')
    tomorrow_str = (now_utc + timedelta(days=1)).strftime('%Y-%m-%d')
    week_ago_str = (now_utc - timedelta(days=7)).strftime('%Y-%m-%d')

    pollutants = {
        "NO2": ("COPERNICUS/S5P/NRTI/L3_NO2", "tropospheric_NO2_column_number_density"),
        "SO2": ("COPERNICUS/S5P/OFFL/L3_SO2", "SO2_column_number_density"),
        "O3": ("COPERNICUS/S5P/NRTI/L3_O3", "O3_column_number_density"),
        "CO": ("COPERNICUS/S5P/NRTI/L3_CO", "CO_column_number_density")
    }

    band_images = []
    date_used = today_str  # Default to today

    for name, (collection_id, band) in pollutants.items():
        
        img = get_mean_image(collection_id, band, week_ago_str, today_str, region)
        date_used = f"{week_ago_str}_to_{today_str}"

        if img is not None:
            img = img.rename(name)
            band_images.append(img)
        else:
            return f"No data available for {name} from {date_used}."

    if band_images:
        # Merge all available bands
        multi_band_image = ee.Image.cat(band_images)
        
        # Export image
        image_path = export_image(multi_band_image, location_name, "Pollutants", date_used, region, scale,filepath)
        print(f"Multi-band image saved to {filepath}")
        return image_path
    else:

        return "No pollutant data of the location is available for export."


