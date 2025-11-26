from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import AuctionListingForm, BidForm
from django.contrib import messages

from .models import User, AuctionListing, Bid


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

@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    bid_form = BidForm()

    if request.method == "POST":
        bid_form = BidForm(request.POST)
        if bid_form.is_valid():
            amount = bid_form.cleaned_data['amount']

            # Get highest bid if exists
            highest_bid = listing.bids.order_by('-amount').first()

            # Validation
            if amount < listing.starting_bid:
                messages.error(request, "Bid must be at least the starting bid.")
            elif highest_bid and amount <= highest_bid.amount:
                messages.error(request, "Bid must be higher than the current highest bid.")
            else:
                # Save bid
                Bid.objects.create(listing=listing, user=request.user, amount=amount)
                listing.current_price = amount
                listing.save()
                messages.success(request, "Your bid was placed successfully!")
                return redirect('listing_detail', listing_id=listing.id)

    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'bid_form': bid_form
    })


@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    if request.user in listing.watchers.all():
        listing.watchers.remove(request.user)
        messages.success(request, "Removed from your Watchlist.")
    else:
        listing.watchers.add(request.user)
        messages.success(request, "Added to your Watchlist.")
    return redirect('listing_detail', listing_id=listing.id)


@login_required
def watchlist_view(request):
    listings = request.user.watchlist.all()
    return render(request, 'auctions/watchlist.html', {'listings': listings})

