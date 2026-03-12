from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    if request.user.role != 'mess':
        return redirect('login')
    return render(request, 'mess_manager/dashboard.html')
