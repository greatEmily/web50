from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import AuctionListingForm

from .models import User, AuctionListing


def index(request):
    listings = AuctionListing.objects.filter(active=True).order_by('-created_at')
    return render(request, "auctions/index.html", {'listings': listings})

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")



@login_required
def create_listing(request):
    if request.method == 'POST':
        form = AuctionListingForm(request.POST, request.FILES)  # ✅ include request.FILES
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.current_price = listing.starting_bid
            listing.save()
            return redirect('index')
    else:
        form = AuctionListingForm()
    return render(request, 'auctions/create_listing.html', {'form': form})


def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    return render(request, 'auctions/listing_detail.html', {'listing': listing})
