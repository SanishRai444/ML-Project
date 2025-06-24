import ee
import logging

# Initialize the Earth Engine API
ee.Initialize(project='ff-sanishrai444')

# Setup logging for the main process
logging.basicConfig(filename='pollution_data_extraction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Setup logging for skipped images with time
skipped_logging = logging.getLogger('skipped_images')
skipped_handler = logging.FileHandler('skipped_images.log')
skipped_handler.setLevel(logging.INFO)
skipped_formatter = logging.Formatter('%(asctime)s - %(message)s')  # Include time in format
skipped_handler.setFormatter(skipped_formatter)
skipped_logging.addHandler(skipped_handler)

# Initialize a counter for skipped images
skipped_count = 0

year = 2023
months = list(range(1, 13))  # Create a list of months (1 to 12)
buffer_size = 3500  # 7 km (3.5 km each side in meters)

# Define a list of locations
locations = [
   # Highly Polluted Cities
    {'name': 'New York City', 'lat': 40.7128, 'lon': -74.0060},  # USA
    {'name': 'Delhi', 'lat': 28.6139, 'lon': 77.2090},  # India
    {'name': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},  # China
    {'name': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437},  # USA
    {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},  # India
    {'name': 'Shanghai', 'lat': 31.2304, 'lon': 121.4737},  # China
    {'name': 'Cairo', 'lat': 30.0444, 'lon': 31.2357},  # Egypt
    {'name': 'Mexico City', 'lat': 19.4326, 'lon': -99.1332},  # Mexico
    {'name': 'Jakarta', 'lat': -6.2088, 'lon': 106.8456},  # Indonesia
    {'name': 'Karachi', 'lat': 24.8607, 'lon': 67.0011},  # Pakistan

    # Intermediate Pollution
    {'name': 'London', 'lat': 51.5074, 'lon': -0.1278},  # UK
    {'name': 'Paris', 'lat': 48.8566, 'lon': 2.3522},  # France
    {'name': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},  # Russia
    {'name': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},  # Japan
    {'name': 'Lagos', 'lat': 6.5244, 'lon': 3.3792},  # Nigeria
    {'name': 'Dhaka', 'lat': 23.8103, 'lon': 90.4125},  # Bangladesh
    {'name': 'Chongqing', 'lat': 29.5630, 'lon': 106.5516},  # China
    {'name': 'Ulaanbaatar', 'lat': 47.8864, 'lon': 106.9057},  # Mongolia
    {'name': 'Tehran', 'lat': 35.6892, 'lon': 51.3890},  # Iran
    {'name': 'Bangkok', 'lat': 13.7563, 'lon': 100.5018},  # Thailand

    # Low Pollution Areas
    {'name': 'Sao Paulo', 'lat': -23.5505, 'lon': -46.6333},  # Brazil
    {'name': 'Rio de Janeiro', 'lat': -22.9068, 'lon': -43.1729},  # Brazil
    {'name': 'Patagonia', 'lat': -47.1787, 'lon': -71.2880},  # Argentina/Chile
    {'name': 'Siberia', 'lat': 60.0000, 'lon': 90.0000},  # Russia
    {'name': 'Amazon Rainforest', 'lat': -3.4653, 'lon': -62.2159},  # Brazil
    {'name': 'Alaska', 'lat': 64.2008, 'lon': -149.4937},  # USA
    {'name': 'Sahara Desert', 'lat': 23.4162, 'lon': 25.6628},  # Africa
    {'name': 'Gobi Desert', 'lat': 42.5000, 'lon': 105.0000},  # Mongolia/China
    {'name': 'Middle East Dust Belt', 'lat': 25.0, 'lon': 50.0},  # Middle East
    {'name': 'Canadian Boreal Forest', 'lat': 56.1304, 'lon': -106.3468},  # Canada

    # Industrial Pollution Hubs
    {'name': 'Houston', 'lat': 29.7604, 'lon': -95.3698},  # USA
    {'name': 'Dubai', 'lat': 25.276987, 'lon': 55.296249},  # UAE
    {'name': 'Essen', 'lat': 51.4556, 'lon': 7.0116},  # Germany
    {'name': 'Johannesburg', 'lat': -26.2041, 'lon': 28.0473},  # South Africa

    # Other Significant Polluted Locations
    {'name': 'Lahore', 'lat': 31.5497, 'lon': 74.3436},  # Pakistan
    {'name': 'Midwest USA', 'lat': 41.2033, 'lon': -98.1420},  # USA
    {'name': 'Kathmandu', 'lat': 27.7172, 'lon': 85.3240},  # Nepal
]

def get_pollution_data(location, month):
    global skipped_count
    try:
        start_date = ee.Date.fromYMD(year, month, 1)
        end_date = start_date.advance(1, 'month')

        # Convert buffer size from meters to degrees
        buffer_degrees = buffer_size / 111320  # 1 degree ≈ 111.32 km

        # Create a rectangular region (7 km × 7 km)
        region = ee.Geometry.Rectangle([
            [location['lon'] - buffer_degrees, location['lat'] - buffer_degrees],  # Bottom-left
            [location['lon'] + buffer_degrees, location['lat'] + buffer_degrees]   # Top-right
        ])

        NO2 = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2')
               .select('tropospheric_NO2_column_number_density')
               .filterDate(start_date, end_date)
               .mean())

        SO2 = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_SO2')
               .select('SO2_column_number_density')
               .filterDate(start_date, end_date)
               .mean())

        O3 = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_O3')
              .select('O3_column_number_density')
              .filterDate(start_date, end_date)
              .mean())

        CO = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_CO')
              .select('CO_column_number_density')
              .filterDate(start_date, end_date)
              .mean())

        # Check if data is available
        if (NO2.bandNames().size().eq(0).getInfo() or
            SO2.bandNames().size().eq(0).getInfo() or
            O3.bandNames().size().eq(0).getInfo() or
            CO.bandNames().size().eq(0).getInfo()):
            skipped_count += 1
            skipped_logging.info(f"Skipped: {location['name']}_Pollution_{year}_{month}")
            return  # Skip this location/month if no data is available

        # Combine bands
        pollution_image = NO2.addBands(SO2).addBands(O3).addBands(CO).clip(region)

        # Export to Google Drive
        task = ee.batch.Export.image.toDrive(
            image=pollution_image,
            description=f"{location['name']}_Pollution_{year}_{month}",
            scale=1000,
            region=region.bounds().getInfo()['coordinates'],  # Get bounding box
            fileFormat='GeoTIFF',
            maxPixels=1e13,
            folder="PollutionData"
        )

        # Start export
        task.start()
        logging.info(f"Export started: {location['name']}_Pollution_{year}_{month}")

    except Exception as e:
        logging.error(f"Error extracting data for {location['name']} during {month}/{year}: {e}")

# Loop over all locations and months
for location in locations:
    for month in months:
        get_pollution_data(location, month)

# After all processing, log the total count of skipped images with time
skipped_logging.info(f"{skipped_count} skipped images in total.")

logging.info("Pollution Data Extraction Process Completed!")
