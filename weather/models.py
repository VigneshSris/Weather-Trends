from django.db import models
class WeatherRecord(models.Model):
    date = models.DateField()
    city = models.CharField(max_length=100, db_index=True)
    temperature_c = models.FloatField()
    humidity = models.FloatField()
    rainfall_mm = models.FloatField()
    def __str__(self):
        return f"{self.city} {self.date} {self.temperature_c}C"
