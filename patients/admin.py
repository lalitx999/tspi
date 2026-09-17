from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['legacy_id', 'full_name', 'phone', 'status', 'created_at']
    list_filter = ['status', 'gender']
    search_fields = ['legacy_id', 'first_name', 'last_name', 'phone', 'hn']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Identity', {'fields': ('legacy_id', 'hn')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'nickname', 'gender', 'birth_date')}),
        ('Contact', {'fields': ('phone', 'email', 'line_id')}),
        ('Address', {'fields': ('address', 'province', 'district', 'subdistrict', 'postcode')}),
        ('Clinical', {'fields': ('status', 'chief_complaint', 'present_illness', 'past_history', 'drug_allergy', 'current_medications')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )
