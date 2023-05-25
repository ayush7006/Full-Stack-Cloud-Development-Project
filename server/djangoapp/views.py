from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarMake,CarModel
from .restapis import get_dealers_from_cf,get_request,get_dealer_by_id_from_cf,get_dealer_reviews_from_cf,post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# View to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# View to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Logging out `{}`...".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("/djangoapp/")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/3e9893f1-9d31-4f3e-a5b7-128fe1b7736e/default/get-dealership"
        # Get dealers from the URL
        #dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        context["dealerships"] = get_dealers_from_cf(url)
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = 'https://us-south.functions.appdomain.cloud/api/v1/web/3e9893f1-9d31-4f3e-a5b7-128fe1b7736e/default/get-review'
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        context = {
            "reviews":  reviews, 
            "dealer_id": dealer_id
        }
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.method == "GET":
        dealersid = dealer_id
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/3e9893f1-9d31-4f3e-a5b7-128fe1b7736e/default/get-dealership?dealerId={0}".format(dealersid)
        # Get dealers from the URL
        context = {
            "cars": CarModel.objects.all(),
            "dealers": get_dealers_from_cf(url),
        }
        return render(request, 'djangoapp/add_review.html', context)
    if request.method == "POST":
        if request.user.is_authenticated:
            form = request.POST
            review = {
                "name": "{request.user.first_name} {request.user.last_name}",
                "dealership": dealer_id,
                "review": form["content"],
                "purchase": form.get("purchasecheck"),
                }
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
                car = CarModel.objects.get(pk=form["car"])
                review["car_make"] = car.carmake.name
                review["car_model"] = car.name
                review["car_year"]= car.year.strftime("%Y")
            json_payload = {"review": review}
            print (json_payload)
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/3e9893f1-9d31-4f3e-a5b7-128fe1b7736e/default/post-review"
            post_request(url, json_payload, dealerId=dealer_id)
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
        else:
            return redirect("/djangoapp/login")