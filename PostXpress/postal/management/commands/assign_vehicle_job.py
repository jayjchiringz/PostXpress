import requests
from django.core.management.base import BaseCommand
from postal.models import Schedule, Station, Vehicle, Driver, Parcel
from django.db.models import Count
import datetime
import random

class Command(BaseCommand):
    help = 'Automatically assign jobs to drivers based on parcel traffic, distance, and timestamp.'

    def handle(self, *args, **kwargs):
        
        def get_coordinates_for_station(station):
            """
            Fetch latitude and longitude for a station using Nominatim (OpenStreetMap) API if not available.
            """
            if station.latitude and station.longitude:
                return True  # Coordinates are already available
            
            address = f"{station.address}, {station.city}, {station.country}"
            url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"

            try:
                response = requests.get(url)
                response.raise_for_status()

                data = response.json()
                if len(data) > 0:
                    location = data[0]
                    station.latitude = location['lat']
                    station.longitude = location['lon']
                    station.save()  # Save the coordinates to the database
                    return True
            except requests.exceptions.RequestException as e:
                print(f"Error fetching coordinates for {station.name}: {e}")

            return False

        def calculate_distance_and_time(origin_station, destination_station):
            """
            Calculate the driving distance and time between two stations using OSRM (Open Source Routing Machine).
            """
            if not origin_station.latitude or not origin_station.longitude or not destination_station.latitude or not destination_station.longitude:
                print("One or both stations do not have valid coordinates.")
                return None, None

            origins = f"{origin_station.latitude},{origin_station.longitude}"
            destinations = f"{destination_station.latitude},{destination_station.longitude}"
            url = f"https://router.project-osrm.org/route/v1/driving/{origins};{destinations}?overview=false"

            try:
                response = requests.get(url)
                response.raise_for_status()

                data = response.json()
                if data['routes']:
                    distance = data['routes'][0]['distance']  # Distance in meters
                    duration = data['routes'][0]['duration']  # Duration in seconds
                    return distance, duration
            except requests.exceptions.RequestException as e:
                print(f"Error fetching distance between {origin_station.name} and {destination_station.name}: {e}")

            return None, None

        def get_highest_traffic_route():
            """
            Get the route (origin-destination pair) with the highest number of unassigned parcels.
            """
            # Group parcels by origin and destination, and count the unassigned parcels
            routes = Parcel.objects.filter(is_assigned=False).values(
                'origin_location', 'destination'
            ).annotate(parcel_count=Count('id')).order_by('-parcel_count')

            if routes.exists():
                return routes[0]  # Return the route with the most unassigned parcels
            return None

        def assign_parcels_to_driver_vehicle(parcels, vehicle, driver):
            """
            Assign parcels to the driver and vehicle, create a schedule, and mark parcels as assigned.
            """
            schedule_date = datetime.date.today()

            # Create a schedule for the driver and vehicle
            schedule = Schedule.objects.create(
                route_code=f"{parcels[0].origin_location}-{parcels[0].destination}",  # Fix: use dot notation
                origin_station=parcels[0].origin_location,  # Fix: use dot notation
                destination_station=parcels[0].destination,  # Fix: use dot notation
                vehicle=vehicle,
                driver=driver,
                departure_time=datetime.time(9, 0),  # Placeholder departure time
                arrival_time=datetime.time(11, 0),  # Placeholder arrival time
                schedule_date=schedule_date
            )

            # Mark the parcels as assigned
            for parcel in parcels:
                parcel.is_assigned = True
                parcel.driver = driver
                parcel.vehicle = vehicle
                parcel.save()

            self.stdout.write(f"Assigned {len(parcels)} parcels to Driver {driver.first_name} {driver.last_name} and Vehicle {vehicle.plate_number}")

        def assign_jobs():
            """
            Main job assignment logic:
            1. Find routes with the most unassigned parcels.
            2. Use OSRM to optimize driver assignment based on distance.
            3. Assign parcels based on route traffic and registration timestamp.
            """
            highest_traffic_route = get_highest_traffic_route()

            if highest_traffic_route:
                # Find unassigned parcels for the route, prioritize by oldest first
                unassigned_parcels = Parcel.objects.filter(
                    origin_location=highest_traffic_route['origin_location'],
                    destination=highest_traffic_route['destination'],
                    is_assigned=False
                ).order_by('created_at')[:10]  # Limit to 10 parcels per schedule for now (can be adjusted)

                # Get all available drivers, including external ones (Uber, Bolt, etc.)
                available_drivers = Driver.objects.filter(available=True)
                available_vehicles = Vehicle.objects.filter(available=True)

                if available_drivers.exists() and available_vehicles.exists():
                    drivers_with_distances = []

                    for driver in available_drivers:
                        # Ensure the driver's current station has valid coordinates
                        if driver.current_station and get_coordinates_for_station(driver.current_station):
                            # Calculate the distance between the driver’s current location and the parcel's origin station
                            driver_distance, _ = calculate_distance_and_time(driver.current_station, unassigned_parcels[0].origin_location)
                            if driver_distance is not None:
                                drivers_with_distances.append((driver, driver_distance))

                    # Sort drivers by shortest distance
                    drivers_with_distances.sort(key=lambda x: x[1])

                    # Assign parcels to the nearest available driver and vehicle
                    if drivers_with_distances:
                        driver = drivers_with_distances[0][0]  # Get the nearest driver
                        vehicle = random.choice(available_vehicles)
                        assign_parcels_to_driver_vehicle(unassigned_parcels, vehicle, driver)
                    else:
                        self.stdout.write("No available drivers with valid routes.")
                else:
                    self.stdout.write("No available drivers or vehicles.")
            else:
                self.stdout.write("No unassigned parcels available for scheduling.")

        # Execute job assignment
        assign_jobs()
