from django.contrib.auth.models import AbstractUser, User
from django.db import models


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
    image = models.ImageField(upload_to='listing_images/', blank=True, null=True)    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    watchers = models.ManyToManyField(User, related_name='watchlist', blank=True)
    owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='listings')

    def __str__(self):
        return self.title


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
