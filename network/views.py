from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import json

from .models import User, Post, Follow


# -------------------------
# INDEX = ALL POSTS PAGE
# -------------------------
def index(request):
    posts = Post.objects.all().order_by("-timestamp")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "network/index.html", {
        "page_obj": page_obj
    })


# -------------------------
# LOGIN / LOGOUT / REGISTER
# -------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })

        login(request, user)
        return HttpResponseRedirect(reverse("index"))

    return render(request, "network/register.html")


# -------------------------
# NEW POST
# -------------------------
@login_required
def new_post(request):
    if request.method == "POST":
        content = request.POST.get("content")
        if content.strip():
            Post.objects.create(user=request.user, content=content)
        return redirect("index")
    return render(request, "network/new_post.html")


# -------------------------
# PROFILE PAGE
# -------------------------
def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user_profile).order_by("-timestamp")

    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Follower counts
    followers_count = Follow.objects.filter(following=user_profile).count()
    following_count = Follow.objects.filter(follower=user_profile).count()

    # Follow status
    is_following = False
    if request.user.is_authenticated and request.user != user_profile:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user_profile
        ).exists()

    return render(request, "network/profile.html", {
        "user_profile": user_profile,
        "page_obj": page_obj,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following
    })


# -------------------------
# FOLLOW / UNFOLLOW
# -------------------------
@login_required
def follow_toggle(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow != request.user:
        existing = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        )
        if existing.exists():
            existing.delete()
        else:
            Follow.objects.create(
                follower=request.user,
                following=user_to_follow
            )

    return redirect("profile", username=username)


# -------------------------
# FOLLOWING FEED
# -------------------------
@login_required
def following(request):
    following_users = Follow.objects.filter(
        follower=request.user
    ).values_list("following", flat=True)

    posts = Post.objects.filter(
        user__in=following_users
    ).order_by("-timestamp")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "page_obj": page_obj
    })


@login_required
def edit_post(request, post_id):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    post = get_object_or_404(Post, id=post_id)

    # SECURITY: Only the owner can edit
    if post.user != request.user:
        return JsonResponse({"error": "You cannot edit someone else's post."}, status=403)

    data = json.loads(request.body)
    new_content = data.get("content", "").strip()

    if new_content == "":
        return JsonResponse({"error": "Content cannot be empty."}, status=400)

    post.content = new_content
    post.save()

    return JsonResponse({"message": "Post updated successfully."}, status=200)

@login_required
def like_toggle(request, post_id):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    post = get_object_or_404(Post, id=post_id)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({
        "liked": liked,
        "like_count": post.likes.count()
    })
