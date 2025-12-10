
from django.contrib import admin
from .models import AuctionListing, Bid, Comment

@admin.register(AuctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'owner', 'category', 'active', 'current_price',
        'starting_bid', 'created_at', 'winner'
    )
    list_filter = ('active', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'winner__username')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'amount', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('listing__title', 'bidder__username')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('listing', 'commenter', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('listing__title', 'commenter__username', 'content')