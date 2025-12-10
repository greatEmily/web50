from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import AuctionListingForm, BidForm, CommentForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch


from .models import User, AuctionListing, Bid, Comment

@login_required(login_url='login')
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
            listing.active = True
            listing.current_price = listing.starting_bid
            listing.save()
            return redirect('index')
    else:
        form = AuctionListingForm()
    return render(request, 'auctions/create_listing.html', {'form': form})


@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)

    # Forms
    bid_form = BidForm()
    comment_form = CommentForm()

    #Data
    highest_bid = listing.bids.order_by('-amount', 'timestamp').first()
    comments = listing.comments.select_related('commenter').order_by('-timestamp')

    if request.method == "POST":
        # Branch: Comment submission
        if 'comment_submit' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                Comment.objects.create(
                    listing=listing,
                    commenter=request.user,
                    content=comment_form.cleaned_data['content']
                )
                messages.success(request, "Your comment has been posted.")
                return redirect('listing_detail', listing_id=listing.id)
            else:
                messages.error(request, "Please correct the comment and try again.")

        # Branch: Bid submission
        if not listing.active:
            messages.error(request, "This listing is closed. You cannot place a bid.")
            return redirect('listing_detail', listing_id=listing.id)

        bid_form = BidForm(request.POST)
        if bid_form.is_valid():
            amount = bid_form.cleaned_data['amount']

            if amount < listing.starting_bid:
                messages.error(request, f"Bid must be at least ${listing.starting_bid}.")
            elif highest_bid and amount <= highest_bid.amount:
                messages.error(request, f"Bid must be higher than ${highest_bid.amount}.")
            else:
                Bid.objects.create(listing=listing, bidder=request.user, amount=amount)
                listing.current_price = amount
                listing.save(update_fields=['current_price'])
                messages.success(request, "Your bid was placed successfully!")
                return redirect('listing_detail', listing_id=listing.id)

    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'bid_form': bid_form,
        'comment_form': comment_form,
        'highest_bid': highest_bid,
        'comments': comments,
        # ✅ Spec support:
        'is_closed': not listing.active,
        'user_is_winner': (listing.winner == request.user) if listing.winner else False,
    })



@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    if request.user in listing.watchers.all():
        listing.watchers.remove(request.user)
        messages.add_message(request, messages.INFO, "Removed from your Watchlist.", extra_tags="watchlist-remove")
    else:
        listing.watchers.add(request.user)
        messages.add_message(request, messages.SUCCESS, "Added to your Watchlist.", extra_tags="watchlist-add")
    return redirect('listing_detail', listing_id=listing.id)



@login_required
def watchlist_view(request):
    listings = request.user.watchlist.all()
    return render(request, 'auctions/watchlist.html', {'listings': listings})


@login_required
def close_listing(request, listing_id):
    if request.method != 'POST':
        raise PermissionDenied  # Only allow POST

    listing = get_object_or_404(AuctionListing, pk=listing_id)

    # Only owner can close
    if request.user != listing.owner:
        raise PermissionDenied

    # Attempt close
    did_close = listing.close(by_user=request.user)
    if not did_close:
        messages.info(request, "This listing is closed.")
    else:

      # Message depending on winner
        if listing.winner:
            messages.success(
                request,
                f"Auction closed. Winner: {listing.winner} at ${listing.current_price}."
            )
        else:
            messages.info(request, "Auction closed. No bids were placed; no winner.")
    return redirect('listing_detail', listing_id=listing.id)



@login_required
def my_listings(request):
    # Fetch all listings created by the logged-in user
    listings = AuctionListing.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'auctions/my_listings.html', {'listings': listings})

