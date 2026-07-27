from units import km_to_miles


def trip_summary(km):
    return f"{km} km is {km_to_miles(km):.1f} miles"
