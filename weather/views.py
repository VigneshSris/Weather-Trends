from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.safestring import mark_safe
from .forms import UploadCSVForm, RegisterForm
from .models import WeatherRecord

import pandas as pd
import json
from io import TextIOWrapper


def home(request):
    """Landing page – redirect to dashboard if logged in."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "weather/home.html")


def register_view(request):
    """User registration."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. You can now log in.")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "weather/register.html", {"form": form})


def login_view(request):
    """User login."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "weather/login.html")


def logout_view(request):
    """Log the user out and redirect home."""
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    """
    Main analytics dashboard:
    - Filters by city / date range
    - Prepares JSON-safe chart data
    - Calculates hottest/coldest days, monthly stats
    """
    city = request.GET.get("city")
    start = request.GET.get("start")
    end = request.GET.get("end")

    qs = WeatherRecord.objects.all()
    if city:
        qs = qs.filter(city__iexact=city)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    context = {}
    if qs.exists():
        df = pd.DataFrame(list(qs.values("date", "temperature_c", "humidity", "rainfall_mm")))
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Daily line chart
        times = df["date"].dt.strftime("%Y-%m-%d").tolist()
        temps = df["temperature_c"].tolist()

        # Monthly averages
        monthly = df.set_index("date").resample("M")["temperature_c"].mean().round(2)
        monthly_labels = [d.strftime("%Y-%m") for d in monthly.index]
        monthly_temps = monthly.tolist()

        # Monthly rainfall
        rain = df.set_index("date").resample("M")["rainfall_mm"].sum().round(2)
        rain_labels = [d.strftime("%Y-%m") for d in rain.index]
        rain_values = rain.tolist()

        # Hottest / coldest day
        hottest_row = df.loc[df["temperature_c"].idxmax()].to_dict()
        coldest_row = df.loc[df["temperature_c"].idxmin()].to_dict()

        # Pass as JSON-safe strings for Chart.js
        context.update({
            "times": mark_safe(json.dumps(times)),
            "temps": mark_safe(json.dumps(temps)),
            "monthly_labels": mark_safe(json.dumps(monthly_labels)),
            "monthly_temps": mark_safe(json.dumps(monthly_temps)),
            "rain_labels": mark_safe(json.dumps(rain_labels)),
            "rain_values": mark_safe(json.dumps(rain_values)),
            "hottest": hottest_row,
            "coldest": coldest_row,
        })

    # City dropdown list
    cities = WeatherRecord.objects.order_by("city").values_list("city", flat=True).distinct()
    context["cities"] = cities

    return render(request, "weather/dashboard.html", context)


@login_required
def upload_csv(request):
    """
    CSV upload view:
    Accepts a file with columns: date, city, temperature_c, humidity, rainfall_mm
    """
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES["csv_file"]
            try:
                text = TextIOWrapper(f.file, encoding="utf-8")
                df = pd.read_csv(text, parse_dates=["date"])

                records = []
                for _, row in df.iterrows():
                    try:
                        rec = WeatherRecord(
                            date=row["date"].date() if hasattr(row["date"], "date") else row["date"],
                            city=str(row["city"]).strip(),
                            temperature_c=float(row.get("temperature_c", 0) or 0),
                            humidity=float(row.get("humidity", 0) or 0),
                            rainfall_mm=float(row.get("rainfall_mm", 0) or 0),
                        )
                        records.append(rec)
                    except Exception:
                        # Skip any malformed rows
                        continue

                if records:
                    WeatherRecord.objects.bulk_create(records)
                    messages.success(request, f"Imported {len(records)} records.")
                else:
                    messages.warning(request, "No valid rows found in CSV.")
                return redirect("dashboard")
            except Exception as e:
                messages.error(request, f"Failed to parse CSV: {e}")
    else:
        form = UploadCSVForm()

    return render(request, "weather/upload.html", {"form": form})