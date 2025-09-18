from django.contrib import admin
from .models import WeatherRecord
from django.utils.safestring import mark_safe
import pandas as pd
import json

@admin.register(WeatherRecord)
class WeatherRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'city', 'temperature_c', 'humidity', 'rainfall_mm')
    list_filter = ('city', 'date')
    search_fields = ('city',)
    ordering = ('-date',)

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        df = pd.DataFrame(list(qs.values('date','temperature_c','rainfall_mm')))
        chart_data = {}
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            chart_data['times'] = df['date'].dt.strftime('%Y-%m-%d').tolist()
            chart_data['temps'] = df['temperature_c'].tolist()
            rain_monthly = df.set_index('date').resample('M')['rainfall_mm'].sum()
            chart_data['rain_labels'] = [d.strftime('%Y-%m') for d in rain_monthly.index]
            chart_data['rain_values'] = rain_monthly.tolist()
        extra_context = extra_context or {}
        extra_context['chart_data'] = mark_safe(json.dumps(chart_data))
        return super().changelist_view(request, extra_context=extra_context)
