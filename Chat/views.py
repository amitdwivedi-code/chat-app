from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from App.models import ChatRequest
from .models import Message
from django.http import JsonResponse
from django.db.models import Q
# Create your views here.

@login_required
def chat_dashboard(request):
    """
    Show all users who have an accepted chat with current user.
    """
    # Users with accepted requests (either sent or received)
    accepted_sent = ChatRequest.objects.filter(
        from_user=request.user, status=ChatRequest.STATUS_ACCEPTED
    ).values_list('to_user_id', flat=True)

    accepted_received = ChatRequest.objects.filter(
        to_user=request.user, status=ChatRequest.STATUS_ACCEPTED
    ).values_list('from_user_id', flat=True)

    accepted_user_ids = list(accepted_sent) + list(accepted_received)
    users = User.objects.filter(id__in=accepted_user_ids)

    context = {
        "users": users
    }
    return render(request, "chat_dashboard.html", context)


@login_required
def chat_history(request, user_id):
    """
    Return chat history between current user and another user.
    """
    other_user = other = get_object_or_404(User, id=user_id)
    qs = Message.objects.filter(
        sender__in=[request.user, other],
        receiver__in=[request.user, other]
    ).order_by('timestamp')

    data = [
        {
            'id': m.id,
            'sender_id': m.sender.id,
            'receiver_id': m.receiver.id,
            'message': m.message,
            'timestamp': m.timestamp.isoformat(),
        } for m in qs
    ]
    # return an array (JS handles both array or {messages: [...]})
    return JsonResponse(data, safe=False)


def fetch_messages(request):
    pass

def send_message(request):
    pass