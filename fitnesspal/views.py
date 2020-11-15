from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login
from django.views import generic
from django.contrib import messages
import requests

from .models import Calories,Exercise,Profile

BASE_URL = 'https://trackapi.nutritionix.com'



def index(request):
    return render(request, 'fitnesspal/index.html')


def calories(request):
    return render(request, 'fitnesspal/calories.html')


def profile(request):
    return render(request, 'fitnesspal/profile.html')


def is_valid_locale(locale: str) -> bool:
    return locale in ['en_US', 'en_GB', 'de_DE', 'fr_FR', 'es_ES']


def get_nutrients_from_nl_query(
        query: str,
        num_servings: float = None,
        aggregate: bool = None,
        line_delimited: bool = None,
        use_raw_foods: bool = None,
        include_subrecipe: bool = None,
        timezone: str = None,
        consumed_at: str = None,
        lat: float = None,
        lng: float = None,
        meal_type: int = None,
        use_branded_foods: bool = None,
        locale: str = None) -> requests.Response:
    """Returns the nutrients for all foods in the posted query.

    Get detailed nutrient breakdown of any natural language text.

    Args:
        query: the query string. Required.
        num_servings: the number of servings this dish yields. The nutrients when this food is logged will be divided by this number.
        aggregate: if present, it combines all the foods into one food object with the food_name equal to the value of this field
        line_delimited: if present, it expects only 1 food per line and will return an array of rules broken if there are any. i.e. 2+ foods on a line, no foods detected on this line, etc
        use_raw_foods: Allows parsing of uncooked variants.
        include_subrecipe: if present, will return recipe composition of the requested food (if exists)
        timezone: timezone in which to parse relative time queries like “yesterday I ate x”
        consumed_at: ISO 8601 compliant date format. Will overwrite any interpreted time contexts.
        lat: latitude
        lng: longitude
        meal_type: meal type
        use_branded_foods: toggle interpretation of branded foods
        locale: locale value for natural food search. Supported values en_US, en_GB, de_DE, fr_FR, es_ES.

    Returns:
        Response
    """
    # default = {
    #     "num_servings": 1,
    #     "line_delimited": False,
    #     "use_raw_foods": False,
    #     "include_subrecipe": False,
    #     "timezone": 'US/Eastern',
    #     "consumed_at": None,
    #     "lat": None,
    #     "lng": None,
    #     "use_branded_foods": False,
    #     "locale": 'en_US',
    # }
    endpoint = '/v2/natural/nutrients'
    # Set the headers
    headers = {
        'Content-Type': 'application/json',  # Set the type of the body sent
        'x-app-id': "73ada124",  # Your Nutritionix Applicatoin ID
        'x-app-key': "679449fb041e2ca7f0fdfc02dc121d9a",  # Your Nutritionix Application Key
        'x-remote-user-id': '0'  # USe 0 for development according to the docs
    }
    # Normally I would just use **kwargs to hold the values, but making it verbose is easier for users
    body = {
        "query": query,
        "num_servings": num_servings,
        "aggregate": aggregate,
        "line_delimited": line_delimited,
        "use_raw_foods": use_raw_foods,
        "include_subrecipe": include_subrecipe,
        "timezone": timezone,
        "consumed_at": consumed_at,
        "lat": lat,
        "lng": lng,
        "meal_type": meal_type,
        "use_branded_foods": use_branded_foods,
        "locale": locale,
    }
    # remove values that aren't set
    for k in [k for k, v in body.items() if v is None]:
        body.pop(k)
    # send a POST request with specified headers and body to API end point
    response = requests.post(url=BASE_URL + endpoint, json=body, headers=headers)
    if response.status_code == 200:
        # Operation successful
        return response
    if response.status_code == 400:
        # Validation error
        return response
    if response.status_code == 500:
        # Base error
        return response
    raise AssertionError('Undocumented response status code')


def calculate_calories(request):
    try:
        res = get_nutrients_from_nl_query(request.POST["food-input"])
    except AssertionError:
        messages.warning(request, "Result not found")
        return render(request, 'fitnesspal/calories.html')
    else:
        cal = res.json()["foods"][0]["nf_calories"]
        name = res.json()["foods"][0]["food_name"]
        pic = res.json()["foods"][0]["photo"]["thumb"]
        size = res.json()["foods"][0]['serving_weight_grams']
        fat = res.json()["foods"][0]["nf_total_fat"]
        # if Calories.objects.filter(food_name = name , calories = cal):
        #     new_food = Calories.objects.filter(food_name = name , calories = cal).first()
        # else:
        new_food = Calories.objects.create(calories = cal, food_name = name)
    return render(request, 'fitnesspal/calories.html', {'new_food' : new_food, 'pic': pic, 'size': size, 'fat': fat})

def add_food_calories(request):
    food = Calories.objects.filter(food_name = request.POST['add_button']).last()
    profile = Profile.objects.filter(user = request.user).first()
    profile.calories_set.add(food)
    return render(request, 'fitnesspal/calories.html')

def profile(request):
    profile = Profile.objects.filter(user = request.user).first()
    total = Calories.objects.filter(user = profile).all()
    return render(request, 'fitnesspal/profile.html', {'total':total})