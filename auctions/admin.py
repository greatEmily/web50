
from django.contrib import admin
from .models import AuctionListing, Bid, Comment, Category

admin.site.register(AuctionListing)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Category)
