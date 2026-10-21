from django.shortcuts import render
from django.http import JsonResponse
# Create your views here.
def liveness(request):
    response = JsonResponse(
        {"status": "ok"},
    )

    return response
