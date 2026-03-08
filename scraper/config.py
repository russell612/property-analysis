"""
Configuration for the property analysis scraper.
Defines target properties, comparables, regions, amenities, and scraping parameters.
"""
import os

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DASHBOARD_PUBLIC_DIR = os.path.join(BASE_DIR, "dashboard", "public", "data")

# Price tiers for grouping
PRICE_TIERS = {
    "budget": {"label": "Budget (< RM 400k)", "min": 0, "max": 400000},
    "mid": {"label": "Mid-Range (RM 400k–700k)", "min": 400000, "max": 700000},
    "upper_mid": {"label": "Upper Mid (RM 700k–1M)", "min": 700000, "max": 1000000},
    "premium": {"label": "Premium (> RM 1M)", "min": 1000000, "max": 99999999},
}

# Amenity categories
AMENITY_TYPES = ["MRT/LRT", "KTM", "Bus", "Supermarket", "Food Court", "Shopping Mall", "School", "Hospital"]

# ===========================
# TARGET PROPERTIES (investor-owned)
# ===========================
PROPERTIES = [
    {
        "name": "Bamboo Hills Residences",
        "alt_names": ["Bamboo Hill Residences", "Bamboo Hills"],
        "developer": "UOA Development Berhad",
        "region": "Bamboo Hills",
        "area": "Segambut",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "total_units": 1762,
        "completion": "2026",
        "is_target": True,
        "price_tier": "mid",
        "propertyguru_id": "19842",
        "propertyguru_slug": "bamboo-hills-residences",
        "edgeprop_id": "48336",
        "edgeprop_listing_id": "439732",
        "edgeprop_slug": "bamboo-hill-residences",
        "edgeprop_area": "kl-city",
        "amenities": {
            "MRT/LRT": {"name": "Bamboo Hills MRT", "distance": "Covered link bridge"},
            "Supermarket": {"name": "Premium grocery (podium)", "distance": "On-site"},
            "Food Court": {"name": "Podium retail F&B", "distance": "On-site"},
            "Shopping Mall": {"name": "Bamboo Hills Podium", "distance": "On-site"},
            "School": {"name": "Sri KDU International School", "distance": "1.5 km"},
            "Hospital": {"name": "KPJ Tawakkal Hospital", "distance": "3 km"},
        },
    },
    {
        "name": "GenStarz",
        "alt_names": ["Gen Starz", "GenStarz OKR", "Gen Starz by Majestic Gen"],
        "developer": "Majestic Gen Sdn Bhd",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "total_units": 360,
        "completion": "Sept 2028",
        "is_target": True,
        "price_tier": "mid",
        "propertyguru_id": "22864",
        "propertyguru_slug": "gen-starz",
        "edgeprop_id": None,
        "edgeprop_slug": None,
        "amenities": {
            "MRT/LRT": {"name": "MRT Kuchai Lama", "distance": "1.2 km"},
            "KTM": {"name": "KTM Pantai Dalam", "distance": "1.5 km"},
            "Supermarket": {"name": "NSK Trade City", "distance": "1 km"},
            "Food Court": {"name": "OKR hawker stalls", "distance": "500m"},
            "Shopping Mall": {"name": "Pearl Point / Mid Valley", "distance": "2 km / 3 km"},
            "School": {"name": "SMK Taman Desa", "distance": "1 km"},
            "Hospital": {"name": "Pantai Hospital KL", "distance": "3 km"},
        },
    },
]

# ===========================
# COMPARABLE PROPERTIES
# ===========================
COMPARABLES = [
    # --- Segambut / Bamboo Hills area ---
    {
        "name": "Scenaria @ North Kiara Hills",
        "alt_names": ["Scenaria North Kiara", "Laman Scenaria Kiara"],
        "developer": "Glomac Bhd",
        "region": "Bamboo Hills",
        "area": "Segambut",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Condominium",
        "total_units": 738,
        "completion": "2017",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": "11323",
        "edgeprop_listing_id": "5660",
        "edgeprop_slug": "scenaria-(laman-scenaria-kiara)",
        "edgeprop_area": "segambut",
        "amenities": {
            "MRT/LRT": {"name": "Sri Delima MRT", "distance": "1 km"},
            "Supermarket": {"name": "Jaya Grocer Desa ParkCity", "distance": "2.5 km"},
            "Food Court": {"name": "Desa ParkCity F&B", "distance": "2 km"},
            "Shopping Mall": {"name": "The Waterfront / Publika", "distance": "2.5 km / 4 km"},
        },
    },
    {
        "name": "United Point Residence",
        "alt_names": ["Residensi Bersepadu", "United Point North Kiara"],
        "developer": "United Point Bhd",
        "region": "Bamboo Hills",
        "area": "Segambut",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "completion": "2020",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "405454",
        "edgeprop_slug": "united-point-residence-(residensi-bersepadu)",
        "edgeprop_area": "segambut",
        "amenities": {
            "MRT/LRT": {"name": "Segambut MRT", "distance": "1.5 km"},
            "Supermarket": {"name": "Jaya Grocer Publika", "distance": "3 km"},
            "Shopping Mall": {"name": "Publika", "distance": "3 km"},
        },
    },
    {
        "name": "Tuan Residency",
        "alt_names": ["Residensi Selingsing", "Tuan Residency Segambut"],
        "developer": "Mah Sing Group",
        "region": "Bamboo Hills",
        "area": "Segambut",
        "city": "Kuala Lumpur",
        "tenure": "Leasehold",
        "property_type": "Service Residence",
        "completion": "2025",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "417362",
        "edgeprop_slug": "tuan-residency-(residensi-selingsing)",
        "edgeprop_area": "segambut",
        "amenities": {
            "MRT/LRT": {"name": "Segambut MRT", "distance": "1.2 km"},
            "Supermarket": {"name": "NSK Kepong", "distance": "2 km"},
            "Food Court": {"name": "Kepong food stalls", "distance": "1.5 km"},
        },
    },
    # --- Old Klang Road area ---
    {
        "name": "OUG Parklane",
        "alt_names": ["Parklane OUG"],
        "developer": "OSK Property",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "total_units": 4225,
        "completion": "2015",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "5103",
        "edgeprop_slug": "oug-parklane",
        "edgeprop_area": "taman-oug",
        "amenities": {
            "MRT/LRT": {"name": "MRT Taman OUG", "distance": "800m"},
            "Bus": {"name": "OUG bus hub", "distance": "500m"},
            "Supermarket": {"name": "NSK OUG", "distance": "1 km"},
            "Food Court": {"name": "OUG food court", "distance": "500m"},
            "Shopping Mall": {"name": "Mid Valley Megamall", "distance": "4 km"},
        },
    },
    {
        "name": "The Scott Garden",
        "alt_names": ["Scott Garden Residence", "Scott Garden OKR"],
        "developer": "WCT Holdings",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "completion": "2014",
        "is_target": False,
        "price_tier": "budget",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "439138",
        "edgeprop_slug": "the-scott-garden",
        "edgeprop_area": "jalan-klang-lama-(old-klang-road)",
        "amenities": {
            "KTM": {"name": "KTM Petaling", "distance": "2 km"},
            "Supermarket": {"name": "Scott Garden retail", "distance": "On-site"},
            "Food Court": {"name": "Scott Garden F&B strip", "distance": "On-site"},
            "Shopping Mall": {"name": "Scott Garden Mall", "distance": "On-site"},
        },
    },
    {
        "name": "Southbank Residence",
        "alt_names": ["Southbank OKR"],
        "developer": "UOA Development Berhad",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Leasehold",
        "property_type": "Service Residence",
        "total_units": 674,
        "completion": "2016",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "458180",
        "edgeprop_slug": "southbank-residence",
        "edgeprop_area": "kuala-lumpur",
        "amenities": {
            "MRT/LRT": {"name": "Mid Valley MRT", "distance": "3 km"},
            "KTM": {"name": "KTM Mid Valley", "distance": "3 km"},
            "Shopping Mall": {"name": "Mid Valley Megamall", "distance": "3 km"},
            "Supermarket": {"name": "Aeon Mid Valley", "distance": "3 km"},
        },
    },
    {
        "name": "Seringin Residences",
        "alt_names": ["Seringin OKR"],
        "developer": "Kerjaya Prospek Group",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Condominium",
        "completion": "2015",
        "is_target": False,
        "price_tier": "premium",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "5843",
        "edgeprop_slug": "seringin-residences",
        "edgeprop_area": "kuchai-lama",
        "amenities": {
            "MRT/LRT": {"name": "MRT Kuchai Lama", "distance": "1 km"},
            "Supermarket": {"name": "Village Grocer Kuchai", "distance": "1.5 km"},
            "Shopping Mall": {"name": "Mid Valley Megamall", "distance": "3 km"},
            "Food Court": {"name": "Kuchai hawker centre", "distance": "1 km"},
        },
    },
    # --- New OKR comparables (closest to GenStarz) ---
    {
        "name": "Verve Suites KL South",
        "alt_names": ["Verve Suites OKR", "Verve KL South"],
        "developer": "Bukit Kiara Properties",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "total_units": 921,
        "completion": "2018",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "198331",
        "edgeprop_slug": "verve-suites-kl-south",
        "edgeprop_area": "jalan-klang-lama-(old-klang-road)",
        "amenities": {
            "MRT/LRT": {"name": "MRT Kuchai Lama", "distance": "1 km"},
            "KTM": {"name": "KTM Pantai Dalam", "distance": "1.5 km"},
            "Supermarket": {"name": "NSK Trade City", "distance": "1 km"},
            "Food Court": {"name": "OKR hawker stalls", "distance": "500m"},
            "Shopping Mall": {"name": "Pearl Point", "distance": "1.5 km"},
        },
    },
    {
        "name": "Millerz Square",
        "alt_names": ["Millerz Square OKR", "Miller Square"],
        "developer": "Exsim Group",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Service Residence",
        "total_units": 1633,
        "completion": "2020",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "414038",
        "edgeprop_slug": "millerz-square",
        "edgeprop_area": "jalan-klang-lama-(old-klang-road)",
        "amenities": {
            "MRT/LRT": {"name": "MRT Kuchai Lama", "distance": "800m"},
            "KTM": {"name": "KTM Petaling", "distance": "2 km"},
            "Supermarket": {"name": "NSK Trade City", "distance": "800m"},
            "Food Court": {"name": "OKR hawker stalls", "distance": "300m"},
            "Shopping Mall": {"name": "Pearl Point / Mid Valley", "distance": "1.5 km / 3 km"},
            "School": {"name": "SMK Taman Desa", "distance": "1.2 km"},
        },
    },
    {
        "name": "D'Ivo Residences",
        "alt_names": ["Divo", "D'Ivo OKR", "D Ivo Residences"],
        "developer": "Sime Darby Property",
        "region": "Old Klang Road",
        "area": "Old Klang Road",
        "city": "Kuala Lumpur",
        "tenure": "Freehold",
        "property_type": "Condominium",
        "total_units": 608,
        "completion": "2025",
        "is_target": False,
        "price_tier": "mid",
        "propertyguru_id": None,
        "propertyguru_slug": None,
        "edgeprop_id": None,
        "edgeprop_listing_id": "450765",
        "edgeprop_slug": "d'ivo-residences",
        "edgeprop_area": "jalan-klang-lama-(old-klang-road)",
        "amenities": {
            "MRT/LRT": {"name": "MRT Kuchai Lama", "distance": "1.2 km"},
            "KTM": {"name": "KTM Pantai Dalam", "distance": "1.5 km"},
            "Supermarket": {"name": "NSK Trade City", "distance": "800m"},
            "Food Court": {"name": "OKR hawker stalls", "distance": "500m"},
            "Shopping Mall": {"name": "Pearl Point", "distance": "On-site (opposite)"},
            "Hospital": {"name": "Pantai Hospital KL", "distance": "3 km"},
        },
    },
]

# All properties combined (targets + comparables)
ALL_PROPERTIES = PROPERTIES + COMPARABLES

# Regions to track for area-level data
REGIONS = [
    {
        "name": "Bamboo Hills / Segambut",
        "brickz_path": "kuala-lumpur/segambut",
        "napic_area": "Segambut",
        "edgeprop_area": "segambut",
    },
    {
        "name": "Old Klang Road",
        "brickz_path": "kuala-lumpur/old-klang-road",
        "napic_area": "Old Klang Road",
        "edgeprop_area": "old-klang-road",
    },
]

# Scraping settings
REQUEST_TIMEOUT = 30000  # ms
PAGE_LOAD_TIMEOUT = 60000  # ms
RATE_LIMIT_DELAY = 1  # seconds between requests
MAX_RETRIES = 3
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
