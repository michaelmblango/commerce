from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User, Category, Listing, Bid, Comment, Watchlist


def index(request):
    active_listings = Listing.objects.filter(active=True).order_by('-created_at')
    return render(request, "auctions/index.html", {
        "listings": active_listings  # Make sure this matches your template
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


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
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        image_url = request.POST.get("image_url", "")
        category_id = request.POST.get("category")

        # Use a try-except block to prevent crashes if category_id is invalid
        category = None
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                category = None

        listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            current_price=starting_bid,
            image_url=image_url,
            category=category,
            creator=request.user
        )
        listing.save()
        return HttpResponseRedirect(reverse("auctions:index"))
    
    # GET request: Render the form with categories from the database
    return render(request, "auctions/create.html", {
        "categories": Category.objects.all()
    })

def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    is_watching = False
    is_creator = False
    is_winner = False
    
    if request.user.is_authenticated:
        is_watching = Watchlist.objects.filter(user=request.user, listing=listing).exists()
        is_creator = listing.creator == request.user
        
        if not listing.active:
            highest_bid = listing.bids.order_by('-amount').first()
            if highest_bid and highest_bid.bidder == request.user:
                is_winner = True
    
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to perform this action.")
            return redirect('auctions:login')
        
        # Handle watchlist toggle
        if "watchlist" in request.POST:
            if is_watching:
                Watchlist.objects.filter(user=request.user, listing=listing).delete()
                messages.success(request, "Removed from watchlist.")
            else:
                Watchlist.objects.create(user=request.user, listing=listing)
                messages.success(request, "Added to watchlist!")
            return redirect('auctions:listing', listing_id=listing_id)
        
        # Handle bid
        if "bid_amount" in request.POST:
            bid_amount = float(request.POST.get("bid_amount"))
            
            if bid_amount <= listing.current_price:
                messages.error(request, "Bid must be higher than current price.")
            else:
                Bid.objects.create(
                    listing=listing,
                    bidder=request.user,
                    amount=bid_amount
                )
                listing.current_price = bid_amount
                listing.save()
                messages.success(request, "Bid placed successfully!")
            return redirect('auctions:listing', listing_id=listing_id)
        
        # Handle comment
        if "comment" in request.POST:
            comment_content = request.POST.get("comment")
            if comment_content:
                Comment.objects.create(
                    listing=listing,
                    commenter=request.user,
                    content=comment_content
                )
                messages.success(request, "Comment added!")
            return redirect('auctions:listing', listing_id=listing_id)
        
        # Handle close listing
        if "close_listing" in request.POST and is_creator:
            listing.active = False
            listing.save()
            messages.success(request, "Listing closed successfully!")
            return redirect('auctions:listing', listing_id=listing_id)
    
    comments = listing.comments.all().order_by('-timestamp')
    bid_count = listing.bids.count()
    highest_bid = listing.bids.order_by('-amount').first()
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "is_watching": is_watching,
        "is_creator": is_creator,
        "is_winner": is_winner,
        "comments": comments,
        "bid_count": bid_count,
        "highest_bid": highest_bid
    })

@login_required
def watchlist(request):
    # Get all watchlist items for the current user
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('listing')
    
    # Extract the listings (both active and inactive)
    listings = [item.listing for item in watchlist_items]
    
    return render(request, "auctions/watchlist.html", {
        "listings": listings,
        "watchlist_count": len(listings)
    })



def categories(request):
    # Get all categories with active listing counts
    categories = Category.objects.all().order_by('name')
    
    # Annotate with active listing count
    from django.db.models import Count, Q
    categories = categories.annotate(
        active_count=Count('listings', filter=Q(listings__active=True))
    )
    
    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    # Only show ACTIVE listings in this category
    listings = Listing.objects.filter(
        category=category, 
        active=True
    ).order_by('-created_at')
    
    return render(request, "auctions/category.html", {
        "category": category,
        "listings": listings
    })