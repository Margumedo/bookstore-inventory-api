from django.contrib import admin

from books.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'isbn',
        'category',
        'stock_quantity',
        'cost_usd',
        'selling_price_local',
        'supplier_country',
        'updated_at',
    )
    list_filter = ('category', 'supplier_country')
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('selling_price_local', 'created_at', 'updated_at')
    ordering = ('-created_at',)
