
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass  # Already provided, you can add extra fields if needed

class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class AuctionListing(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Bid(models.Model):
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} by {self.bidder}"

class Comment(models.Model):
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter}"
