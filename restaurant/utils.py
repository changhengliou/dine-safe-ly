from django.conf import settings
from django.forms.models import model_to_dict
from .models import InspectionRecords, Restaurant, YelpRestaurantDetails
import requests
import json


def get_restaurant_info_yelp(business_id):
    access_token = settings.YELP_ACCESS_TOKE
    headers = {"Authorization": "bearer %s" % access_token}
    url = settings.YELP_BUSINESS_API + business_id
    return requests.get(url, headers=headers)


def get_restaurant_reviews_yelp(business_id):
    access_token = settings.YELP_TOKEN_1
    headers = {"Authorization": "bearer %s" % access_token}
    url = settings.YELP_BUSINESS_API + business_id + "/reviews"
    return requests.get(url, headers=headers)


def merge_yelp_info(restaurant_info, restaurant_reviews):
    return {
        "info": json.loads(restaurant_info.content),
        "reviews": json.loads(restaurant_reviews.content),
    }


def query_yelp(business_id):
    if not business_id:
        return None
    restaurant_info = get_restaurant_info_yelp(business_id)
    restaurant_reviews = get_restaurant_reviews_yelp(business_id)

    data = merge_yelp_info(restaurant_info, restaurant_reviews)
    return data


def get_latest_inspection_record(business_name, business_address, postcode):
    records = InspectionRecords.objects.filter(
        restaurant_name=business_name,
        business_address=business_address,
        postcode=postcode,
    ).order_by("-inspected_on")
    if len(records) >= 1:
        record = model_to_dict(records[0])
        record["inspected_on"] = record["inspected_on"].strftime("%Y-%m-%d %I:%M %p")
        return record

    return None


def query_inspection_record(business_name, business_address, postcode):
    records = InspectionRecords.objects.filter(
        restaurant_name=business_name,
        business_address=business_address,
        postcode=postcode,
    ).order_by("-inspected_on")
    result = []
    for record in records:
        inspection_record = model_to_dict(record)
        inspection_record["inspected_on"] = inspection_record["inspected_on"].strftime(
            "%Y-%m-%d %I:%M %p"
        )
        result.append(inspection_record)

    return result


def get_restaurant_list(
    page, limit, keyword=None, neighbourhoods_filter=None, categories_filter=None
):
    page = int(page) - 1
    offset = int(page) * int(limit)
    if keyword:
        restaurants = Restaurant.objects.filter(restaurant_name__contains=keyword)[
            offset : offset + int(limit)  # noqa: E203
        ]
    else:
        restaurants = Restaurant.objects.all()[
            offset : offset + int(limit)  # noqa: E203
        ]
    result = []
    for restaurant in restaurants:
        restaurant_dict = model_to_dict(restaurant)
        restaurant_dict["yelp_info"] = (
            json.loads(get_restaurant_info_yelp(restaurant.business_id).content)
            if restaurant.business_id
            else None
        )
        latest_inspection_record = get_latest_inspection_record(
            restaurant.restaurant_name, restaurant.business_address, restaurant.postcode
        )
        restaurant_dict["latest_record"] = latest_inspection_record
        result.append(restaurant_dict)
    return result


def get_filtered_restaurants(price, neighborhood, rating, category, page, limit):
    filters = {}
    offset = int(page - 1) * int(limit)
    if price:
        filters["price__in"] = price
    if neighborhood:
        filters["neighborhood__in"] = neighborhood
    if rating:
        filters["rating__gte"] = rating
    if category:
        filters["category__in"] = category

    filtered_restaurants = YelpRestaurantDetails.objects.filter(**filters)[
        offset : offset + int(limit)
    ]
    return filtered_restaurants
