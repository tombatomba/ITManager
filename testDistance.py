import math

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

import math

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def distanceMatrix(itemList, radius_km):
    names = [item["itemName"] for item in itemList]

    # inicijalizacija matrice
    matrix = {
        name: {other: None for other in names}
        for name in names
    }

    for i, item1 in enumerate(itemList):
        for j, item2 in enumerate(itemList):

            if i == j:
                continue  # preskačemo sebe

            dist = haversine_km(
                item1["Latitude"], item1["Longitude"],
                item2["Latitude"], item2["Longitude"]
            )

            if dist <= radius_km:
                matrix[item1["itemName"]][item2["itemName"]] = round(dist, 2)

    return matrix



def findNeighbours(itemList, radius_km):
    """
    itemList: [
        {"itemName": "A", "Latitude": 44.8, "Longitude": 20.4},
        ...
    ]
    radius_km: float
    """

    neighbours = {}

    for i, item in enumerate(itemList):
        name1 = item["itemName"]
        lat1 = item["Latitude"]
        lon1 = item["Longitude"]

        neighbours[name1] = []

        for j, other in enumerate(itemList):
            if i == j:
                continue

            dist = haversine_km(
                lat1, lon1,
                other["Latitude"], other["Longitude"]
            )

            if dist <= radius_km:
                neighbours[name1].append({
                    "itemName": other["itemName"],
                    "distanceKm": round(dist, 2)
                })

    return neighbours


items = [
    {"itemName": "Beograd", "Latitude": 44.786568, "Longitude": 20.448922},
    {"itemName": "Novi Sad", "Latitude": 45.267135, "Longitude": 19.833550},
    {"itemName": "Niš", "Latitude": 43.320902, "Longitude": 21.895759},
    {"itemName": "Kragujevac", "Latitude": 44.016521, "Longitude": 20.916670},
    {"itemName": "Subotica", "Latitude": 46.100547, "Longitude": 19.665059},
    {"itemName": "Zrenjanin", "Latitude": 45.381561, "Longitude": 20.368574},
    {"itemName": "Pančevo", "Latitude": 44.874000, "Longitude": 20.647567},
    {"itemName": "Smederevo", "Latitude": 44.665894, "Longitude": 20.933517},
    {"itemName": "Kruševac", "Latitude": 43.575755, "Longitude": 21.331051},
    {"itemName": "Kraljevo", "Latitude": 43.723848, "Longitude": 20.687254},
    {"itemName": "Čačak", "Latitude": 43.891414, "Longitude": 20.350165},
    {"itemName": "Valjevo", "Latitude": 44.268273, "Longitude": 19.890655},
    {"itemName": "Leskovac", "Latitude": 42.996376, "Longitude": 21.944034},
    {"itemName": "Novi Pazar", "Latitude": 43.140698, "Longitude": 20.521362},
    {"itemName": "Subotica", "Latitude": 46.100547, "Longitude": 19.665059},
    {"itemName": "Šabac", "Latitude": 44.750000, "Longitude": 19.690000},
    {"itemName": "Vranje", "Latitude": 42.545034, "Longitude": 21.900271},
    {"itemName": "Zaječar", "Latitude": 43.901505, "Longitude": 22.273801},
    {"itemName": "Sremska Mitrovica", "Latitude": 44.970165, "Longitude": 19.612413},
    {"itemName": "Sombor", "Latitude": 45.772740, "Longitude": 19.114704},
    {"itemName": "Kikinda", "Latitude": 45.829910, "Longitude": 20.463380}
]

#stampaj susede po kriterijumu
result = findNeighbours(items, 30)
for k, v in result.items():
    print(k, "→", v)

matrix = distanceMatrix(items, 500)
for row, cols in matrix.items():
    print(row, cols)

import pandas as pd

df = pd.DataFrame(matrix)
print(df)

from werkzeug.security import generate_password_hash

# Generiši hash za lozinku "admin123"
hashed_pw = generate_password_hash("admin123")
print('Paasword:',hashed_pw) 
# Ovo će vratiti nešto tipa: 'pbkdf2:sha256:260000$...'
# Taj dugi string upiši u SQL kolonu Password za tvog korisnika.
#scrypt:32768:8:1$nt5UXJldVLlltd3M$1095079e41c918f6046012a76561204b4796f6d7ce0ce7081d2f0f8081db6f338cd5e8f5ee641af93d8c0c7edf6716cb538d2771033aa51c0be54c195b0c3f94