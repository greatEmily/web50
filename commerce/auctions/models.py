from django.contrib.auth.models import AbstractUser, User
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    pass


CATEGORY_CHOICES = [
    ('Fashion', 'Fashion'),
    ('Toys', 'Toys'),
    ('Electronics', 'Electronics'),
    ('Home', 'Home'),
    ('Other', 'Other'),
]

class AuctionListing(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(
        upload_to='listing_images/',
        blank=True,
        null=True,
        default='listing_images/default.jpg'  # <-- ensure this file exists under MEDIA_ROOT
    )   
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    watchers = models.ManyToManyField(User, related_name='watchlist', blank=True)
    owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='listings')

    
    # Auction outcome / audit
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='won_auctions'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='closed_listings'
    )



    def __str__(self):
        return self.title
    
    
    @transaction.atomic
    def close(self, by_user):
        """
        Close the auction: mark inactive, set winner if highest bid exists,
        freeze the current_price, and record audit fields atomically.
        """
        if not self.active:
            return False  # already closed

        # Determine highest bid (if any)
        highest_bid = self.bids.order_by('-amount', 'timestamp').first()

        # Persist state
        self.active = False
        self.closed_at = timezone.now()
        self.closed_by = by_user

        if highest_bid:
            self.winner = highest_bid.bidder
            self.current_price = highest_bid.amount

        self.save(update_fields=[
            'active', 'closed_at', 'closed_by', 'winner', 'current_price'
        ])



class Bid(models.Model):
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey('User', on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} by {self.bidder.username}"



class Comment(models.Model):
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey('User', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter.username} on {self.listing.title}"
