from django.contrib import admin
from .models import WeatherRecord
@admin.register(WeatherRecord)
class WeatherRecordAdmin(admin.ModelAdmin):
    list_display = ('date','city','temperature_c','humidity','rainfall_mm')
    list_filter = ('city',)
    search_fields = ('city',)
