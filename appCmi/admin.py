from django.contrib import admin
from .models import FAQ, FAQImage, FAQReaction, FAQTag, FAQTagAssignment

# Register your models here.
class FAQImageInline(admin.TabularInline):
    model = FAQImage
    extra = 1

class FAQTagAssignmentInline(admin.TabularInline):
    model = FAQTagAssignment
    extra = 1

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_by', 'is_active', 'created_at', 'total_reactions']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    inlines = [FAQImageInline, FAQTagAssignmentInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new FAQ
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(FAQTag)
class FAQTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(FAQReaction)
class FAQReactionAdmin(admin.ModelAdmin):
    list_display = ['faq', 'user', 'created_at']
    list_filter = ['created_at']