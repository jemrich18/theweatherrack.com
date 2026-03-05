from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import HuntingArea
from .forms import HuntingAreaForm
from .utils import geocode_location, get_scored_forecast

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'hunt/register.html', {'form': form})

@login_required
def dashboard(request):
    areas = HuntingArea.objects.filter(user=request.user)
    return render(request, 'hunt/dashboard.html', {'areas': areas})

from .utils import geocode_location

@login_required
def add_area(request):
    if request.method == 'POST':
        form = HuntingAreaForm(request.POST)
        if form.is_valid():
            location = geocode_location(form.cleaned_data['location_search'])
            if location:
                area = form.save(commit=False)
                area.user = request.user
                area.latitude = location['latitude']
                area.longitude = location['longitude']
                area.save()
                messages.success(request, f"Area added: {location['display_name']}")
                return redirect('dashboard')
            else:
                messages.error(request, 'Location not found. Try being more specific.')
    else:
        form = HuntingAreaForm()
    return render(request, 'hunt/add_area.html', {'form': form})

@login_required
def delete_area(request, pk):
    area = get_object_or_404(HuntingArea, pk=pk, user=request.user)
    if request.method == 'POST':
        area.delete()
        messages.success(request, 'Hunting area deleted.')
    return redirect('dashboard')

from .utils import geocode_location, get_scored_forecast

@login_required
def area_forecast(request, pk):
    area = get_object_or_404(HuntingArea, pk=pk, user=request.user)
    forecast = get_scored_forecast(area.latitude, area.longitude)
    return render(request, 'hunt/forecast.html', {
        'area': area,
        'forecast': forecast
    })

@login_required
def area_forecast(request, pk):
    area = get_object_or_404(HuntingArea, pk=pk, user=request.user)
    forecast = get_scored_forecast(area.latitude, area.longitude)
    return render(request, 'hunt/forecast.html', {
        'area': area,
        'forecast': forecast
    })