from diplomacy.models import Game
from django.shortcuts import render_to_response, get_object_or_404

def index(request):
    latest_game_list = Game.objects.all().order_by('-created')[:5]
    return render_to_response('index.html',
                              {'latest_game_list': latest_game_list})

def detail(request, game_id):
    g = get_object_or_404(Game, pk=game_id)
    return render_to_response('detail.html', {'game': g})
