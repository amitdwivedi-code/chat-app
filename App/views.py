from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .forms import ProfileForm, PostForm
from django.contrib.auth.decorators import login_required
from .models import Profile, ChatRequest, Post, Like, Comment, Notification
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
from .utils import notify_user

# Create your views here.

def Index(request):
    """
    Handles register and login from the same page.
    Uses PRG (Post/Redirect/Get) so refreshing won't resubmit a POST.
    Redirects include ?show=login or ?show=register so the template can toggle which form to display.
    """
    if request.user.is_authenticated:
        return redirect("/home", username=request.user.username)

    if request.method == "POST":
        # ---------- REGISTER ----------
        if "register_submit" in request.POST:
            username = (request.POST.get("username") or "").strip()
            email = (request.POST.get("email") or "").strip()
            password = request.POST.get("password") or ""
            confirm_password = request.POST.get("confirm_password") or ""

            # basic validation
            if not username:
                messages.error(request, "Username is required.")
                return redirect(f"{reverse('index')}?show=register")

            if not email:
                messages.error(request, "Email is required.")
                return redirect(f"{reverse('index')}?show=register")

            if not password:
                messages.error(request, "Password is required.")
                return redirect(f"{reverse('index')}?show=register")

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect(f"{reverse('index')}?show=register")

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect(f"{reverse('index')}?show=register")

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return redirect(f"{reverse('index')}?show=register")

            # all good -> create user and redirect to login view of same page
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Registration successful. Please log in.")
            return redirect(f"{reverse('index')}?show=login")  # PRG

        # ---------- LOGIN ----------
        elif "login_submit" in request.POST:
            username = (request.POST.get("username") or "").strip()
            password = request.POST.get("password") or ""

            if not username or not password:
                messages.error(request, "Please provide username and password.")
                return redirect(f"{reverse('index')}?show=login")

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # redirect to the chat room (adjust target if you have a different dashboard)
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
                return redirect(f"{reverse('index')}?show=login")
        else:
            messages.error(request, "Invalid form submission.")
            return redirect(reverse("index"))
    return render(request, "index.html")

def logoutUser(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("index")  # redirect to your login/home page

@login_required
def Home(request):
    # All users except current

    users = User.objects.exclude(pk=request.user.pk)
    
    # notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]

    # Requests sent by me
    sent_requests = ChatRequest.objects.filter(from_user=request.user)
    sent_map = {req.to_user_id: req for req in sent_requests}

    # Incoming requests to me (pending)
    incoming_requests = ChatRequest.objects.filter(
        to_user=request.user,
        status=ChatRequest.STATUS_PENDING
    )
    incoming_user_ids = incoming_requests.values_list("from_user_id", flat=True)

    # Users whose requests I already accepted
    accepted_incoming_ids = ChatRequest.objects.filter(
        to_user=request.user,
        status=ChatRequest.STATUS_ACCEPTED
    ).values_list("from_user_id", flat=True)

    # Exclude:
    users = (
        users.exclude(id__in=incoming_user_ids)
        .exclude(id__in=accepted_incoming_ids)
        .order_by("username")
    )

    # Profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    # Forms
    profile_form = ProfileForm(instance=profile)
    post_form = PostForm()

    if request.method == "POST":
        if "profile_submit" in request.POST:  # profile update
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                p = profile_form.save(commit=False)
                p.user = request.user
                p.save()
                messages.success(request, "✅ Your profile has been saved.")
                return redirect("home")
            else:
                messages.error(request, "Please correct the errors in profile form.")

        elif "post_submit" in request.POST:  # new post
            post_form = PostForm(request.POST, request.FILES)
            if post_form.is_valid():
                new_post = post_form.save(commit=False)
                new_post.author = request.user
                new_post.save()
                messages.success(request, "✅ Post created successfully.")
                return redirect("home")
            else:
                messages.error(request, "Please correct the errors in post form.")

    # ✅ Get posts from me + my accepted friends
    friend_ids = ChatRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)),
        status=ChatRequest.STATUS_ACCEPTED
    ).values_list("from_user_id", "to_user_id")

    # Flatten into list of ids
    friend_ids = set([uid for pair in friend_ids for uid in pair])
    friend_ids.add(request.user.id)  # include myself

    posts = (
        Post.objects.filter(author_id__in=friend_ids)
            .select_related("author")
            .prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("user").order_by("created_at")
                )
            )
            .order_by("-created_at")
    )

    for p in posts:
        all_comments = list(p.comments.all())              # already prefetched
        p.comments_list = all_comments                    # full list, oldest → newest
        p.recent_comments = all_comments[-2:] if all_comments else []  # last 2 (most recent)
        p.more_comments = len(all_comments) > len(p.recent_comments)


    context = {
        "users": users,
        "sent_map": sent_map,
        "incoming_requests": incoming_requests,
        "profile": profile,
        "profile_form": profile_form,
        "posts": posts,
        "post_form": post_form,
        "notifications": notifications,
    }
    return render(request, "home.html", context)


@login_required
def send_request(request, user_id):
    if request.method == "POST":
        to_user = get_object_or_404(User, pk=user_id)
        
        # Avoid sending request to self
        if to_user == request.user:
            messages.error(request, "You cannot send a request to yourself.")
            return redirect("home")

        # Check if request already exists
        existing = ChatRequest.objects.filter(from_user=request.user, to_user=to_user).first()
        if existing:
            messages.warning(request, "Chat request already sent.")
        else:
            req = ChatRequest.objects.create(from_user=request.user, to_user=to_user, status=ChatRequest.STATUS_PENDING)
            messages.success(request, f"Chat request sent to {to_user.username}.")
            Notification.objects.create(
                user=to_user,              # receiver
                actor=request.user,        # sender
                verb="sent you a chat request",
                target_id=req.id,
                target_type="chat_request"
            )

            notify_user(
                user_id=to_user.id,    # send to the receiver, not the sender
                message=f"{request.user.username} sent you a chat request"
            )
                        
    return redirect("home")


@login_required
def respond_request(request, req_id):
    if request.method == "POST":
        req = get_object_or_404(ChatRequest, pk=req_id, to_user=request.user)

        action = request.POST.get("action")
        if action == "accept":
            req.status = ChatRequest.STATUS_ACCEPTED
            req.save()
            messages.success(request, f"You accepted the chat request from {req.from_user.username}.")
            Notification.objects.create(
                user=req.from_user,     # who should receive the notification
                actor=request.user,     # who performed the action
                verb="accepted your chat request",
                target_id=req.id,
                target_type="chat_request"
            )

            notify_user(
                user_id=req.from_user.id,
                message=f"{request.user.username} accepted your chat request"
            )

        elif action == "decline":
            req.status = ChatRequest.STATUS_DECLINED
            req.save()
            messages.success(request, f"You declined the chat request from {req.from_user.username}.")
            Notification.objects.create(
                user=req.from_user,
                actor=request.user,
                verb="declined your chat request",
                target_id=req.id,
                target_type="chat_request"
            )

            notify_user(
                user_id=req.from_user.id,
                message=f"{request.user.username} declined your chat request"
            )
        else:
            messages.error(request, "Invalid action.")
    return redirect("home")


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        # Toggle: user already liked -> unlike
        like.delete()
        liked = False
    else:
        liked = True

        if post.author != request.user:
            Notification.objects.create(
                user=post.author,        # who will receive notification (post owner)
                actor=request.user,      # who liked the post
                verb="liked your post",
                target_id=post.id,
                target_type="post"
            )
        notify_user(
                user_id=post.author.id,
                message=f"{request.user.username} liked your post '{post.title}'"
            )

    return JsonResponse({
        "liked": liked,
        "likes_count": post.likes.count(),
    })


@login_required
@require_POST
def add_comment(request, post_id):
    from .models import Post, Comment

    text = request.POST.get("text")
    if not text.strip():
        return JsonResponse({"error": "Comment cannot be empty"}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    # Create comment
    comment = Comment.objects.create(
        post=post,
        user=request.user,
        text=text
    )

    if post.author != request.user:
        Notification.objects.create(
            user=post.author,         # post owner
            actor=request.user,       # who commented
            verb="commented on your post",
            target_id=post.id,
            target_type="post"
        )

    notify_user(
            user_id=post.author.id,
            message=f"{request.user.username} commented on your post '{post.title}'"
        )

    return JsonResponse({
        "user": comment.user.username,
        "text": comment.text,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
        "comments_count": post.comments.count(),
    })


@login_required
def User_Profile(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None

    # Handle POST request for profile creation/update
    if request.method == "POST" and "profile_submit" in request.POST:
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            p = profile_form.save(commit=False)
            p.user = request.user
            p.save()
            messages.success(request, "Your profile has been saved.")
            return redirect("home")
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        profile_form = ProfileForm(instance=profile)

    # User posts
    posts = Post.objects.filter(author=user).order_by('-created_at')

    # Following = accepted requests where current user is sender
    following = ChatRequest.objects.filter(
        from_user=user,
        status=ChatRequest.STATUS_ACCEPTED
    ).select_related("to_user")

    # Followers = accepted requests where current user is receiver
    followers = ChatRequest.objects.filter(
        to_user=user,
        status=ChatRequest.STATUS_ACCEPTED
    ).select_related("from_user")

    context = {
        'profile': profile,
        'posts': posts,
        'followers_count': followers.count(),
        'following_count': following.count(),
        'profile_form': profile_form,  # pass the form to template
        'show_profile': True,
        'show_post_form': True,
    }

    return render(request, 'profile.html', context)



@login_required
def create_post(request):
    user = request.user

    # Check if profile exists
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        messages.info(request, "You need to create your profile before posting.")
        return redirect("create_profile")  # make sure this URL name exists

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            new_post = post_form.save(commit=False)
            new_post.author = user
            new_post.save()
            messages.success(request, "Post created successfully.")
            return redirect("home")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        post_form = PostForm()

    context = {
        "post_form": post_form,
        "profile": profile
    }
    return render(request, 'post.html', context)
