import datetime
import random  # Ensure random is imported
from django.core.exceptions import ObjectDoesNotExist
from postal.models import Schedule, Station, Vehicle, Driver

def assign_vehicle_to_driver():
    # Get all available drivers
    available_drivers = Driver.objects.filter(available=True)

    # Get all available vehicles
    available_vehicles = Vehicle.objects.filter(available=True)

    # Ensure there are available drivers and vehicles
    if available_drivers.exists() and available_vehicles.exists():
        # Randomly select a driver
        driver = random.choice(available_drivers)

        # Randomly select a vehicle
        vehicle = random.choice(available_vehicles)

        # Assign the vehicle to the driver
        driver.assigned_vehicle = vehicle
        driver.available = False  # Mark the driver as unavailable
        vehicle.available = False  # Mark the vehicle as unavailable
        driver.save()
        vehicle.save()

        print(f"Assigned Vehicle {vehicle.vehicle_number} to Driver {driver.name}")
        return driver, vehicle
    else:
        print("No available drivers or vehicles")
        return None, None

def populate_schedules():
    try:
        origin_station = Station.objects.get(code="00100")  # Example origin (G.P.O Nairobi)
        destination_station = Station.objects.get(code="00521")  # Example destination (Embakasi)
        vehicle = Vehicle.objects.get(vehicle_number="KBD 123A")
        driver = Driver.objects.get(name="John Doe")

        schedule_date = datetime.date.today()

        schedule = Schedule.objects.create(
            route_code="NAI-EMB",
            origin_station=origin_station,
            destination_station=destination_station,
            vehicle=vehicle,
            driver=driver,
            departure_time=datetime.time(9, 0),  # 9:00 AM
            arrival_time=datetime.time(11, 0),  # 11:00 AM
            schedule_date=schedule_date
        )
        print(f"Schedule created: {schedule}")
        return schedule
    except ObjectDoesNotExist as e:
        print(f"Error: {e}")
        return None

# Main function to run the code
def main():
    # First, assign a vehicle to a driver
    driver, vehicle = assign_vehicle_to_driver()

    # Only create a schedule if both a driver and vehicle were assigned
    if driver and vehicle:
        populate_schedules()

# Entry point for running the script
if __name__ == "__main__":
    main()
