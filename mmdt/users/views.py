from django.shortcuts import render, redirect
from django.contrib.auth import login
from users.forms import CustomUserCreationForm


def register(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            next_param = request.GET.get("next")
            if next_param:
                return redirect(next_param)
            return redirect("/")
    return render(request, "users/register.html", {"form": form})
