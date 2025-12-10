
from django import forms
from .models import AuctionListing, Comment


class AuctionListingForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ['title', 'description', 'starting_bid', 'image', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'starting_bid': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class BidForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Your Bid")


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        label="Add a comment",
        widget=forms.Textarea(attrs={
            "rows": 1,
            "placeholder": "Share your thoughts about this listing..."
        })
    )

    class Meta:
        model = Comment
        fields = ["content"]
