import requests
from django.core.management.base import BaseCommand
from postal.models import Station

class Command(BaseCommand):
    help = 'Populate missing latitude and longitude coordinates for all stations.'

    def handle(self, *args, **kwargs):
        # Query all stations that are missing coordinates (latitude and/or longitude)
        stations = Station.objects.filter(latitude__isnull=True, longitude__isnull=True)

        if not stations.exists():
            self.stdout.write("All stations already have coordinates.")
            return

        # Base URL for Nominatim API (OpenStreetMap)
        nominatim_url = "https://nominatim.openstreetmap.org/search"

        for station in stations:
            # Create the search query using the station's office name (which is the town or city)
            params = {
                'q': station.office,  # The name of the town or city
                'format': 'json',  # Response format
                'limit': 1  # We only want the top result
            }

            try:
                # Make the request to the Nominatim API
                response = requests.get(nominatim_url, params=params)
                response.raise_for_status()  # Raise an error for bad status codes

                # Parse the response JSON
                data = response.json()

                # Check if we got a result
                if data:
                    location = data[0]  # The top result
                    station.latitude = location['lat']
                    station.longitude = location['lon']
                    station.save()  # Save the updated station coordinates

                    self.stdout.write(f"Updated {station.office}: (Lat: {station.latitude}, Lon: {station.longitude})")
                else:
                    self.stdout.write(f"No coordinates found for {station.office}.")

            except requests.exceptions.RequestException as e:
                self.stdout.write(f"Error fetching coordinates for {station.office}: {e}")

        self.stdout.write("Finished updating station coordinates.")
