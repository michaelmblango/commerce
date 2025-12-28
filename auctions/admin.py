from django.contrib import admin
from django.utils.html import format_html
from .models import User, Listing, Bid, Comment, Watchlist, Category


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'listing_count')
    search_fields = ('name',)
    ordering = ('name',)
    
    def listing_count(self, obj):
        count = obj.listings.filter(active=True).count()
        return format_html('<span style="color: green; font-weight: bold;">{} active</span>', count)
    listing_count.short_description = 'Active Listings'


class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'current_price', 'category', 'status_badge', 'created_at', 'bid_count')
    list_filter = ('active', 'category', 'created_at')
    search_fields = ('title', 'description', 'creator__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'creator')
        }),
        ('Pricing', {
            'fields': ('starting_bid', 'current_price')
        }),
        ('Categorization', {
            'fields': ('category', 'image_url')
        }),
        ('Status', {
            'fields': ('active', 'created_at')
        }),
    )
    
    def status_badge(self, obj):
        if obj.active:
            return format_html(
                '<span style="color: white; background: green; padding: 3px 10px; border-radius: 3px;">{}</span>',
                'Active'
            )
        return format_html(
            '<span style="color: white; background: red; padding: 3px 10px; border-radius: 3px;">{}</span>',
            'Closed'
        )
    status_badge.short_description = 'Status'
    
    def bid_count(self, obj):
        count = obj.bids.count()
        suffix = 's' if count != 1 else ''
        return format_html('<strong>{} bid{}</strong>', count, suffix)
    bid_count.short_description = 'Bids'


class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'amount_display', 'timestamp')
    list_filter = ('timestamp', 'listing')
    search_fields = ('listing__title', 'bidder__username')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def amount_display(self, obj):
        return format_html('<span style="color: green; font-weight: bold;">${}</span>', obj.amount)
    amount_display.short_description = 'Bid Amount'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'commenter', 'listing', 'timestamp')
    list_filter = ('timestamp', 'listing')
    search_fields = ('content', 'commenter__username', 'listing__title')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Comment'


class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'listing_status')
    list_filter = ('listing__active',)
    search_fields = ('user__username', 'listing__title')
    
    def listing_status(self, obj):
        if obj.listing.active:
            return format_html('<span style="color: green;">●</span> {}', 'Active')
        return format_html('<span style="color: red;">●</span> {}', 'Closed')
    listing_status.short_description = 'Listing Status'


# Register models with custom admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Watchlist, WatchlistAdmin)

# Customize admin site headers
admin.site.site_header = "AuctionHub Administration"
admin.site.site_title = "AuctionHub Admin"
admin.site.index_title = "Welcome to AuctionHub Admin Panel"