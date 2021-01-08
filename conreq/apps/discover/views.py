# from django.shortcuts import render
from conreq import content_discovery
from conreq.apps.helpers import (
    STATIC_CONTEXT_VARS,
    generate_context,
    set_many_conreq_status,
)
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.template.loader import render_to_string

# Create your views here.
@login_required
def discover(request):
    # Get the page number from the URL
    page = int(request.GET.get("page", 1))
    # Get the content type from the URL
    content_type = request.GET.get("content_type", None)

    # Search for TV content if requested
    if content_type == "tv":
        tmdb_results = content_discovery.tv(page, page_multiplier=2)["results"]
        active_tab = STATIC_CONTEXT_VARS["tv_shows"]

    # Search for movie content if requested
    elif content_type == "movie":
        tmdb_results = content_discovery.movies(page, page_multiplier=2)["results"]
        active_tab = STATIC_CONTEXT_VARS["movies"]

    # Search for both content if requested
    else:
        tmdb_results = content_discovery.all(page)["results"]
        active_tab = STATIC_CONTEXT_VARS["combined"]

    template = loader.get_template("primary/base.html")

    # Set conreq status for all cards
    set_many_conreq_status(tmdb_results)

    context = generate_context(
        {
            "all_cards": tmdb_results,
            "active_tab": active_tab,
        }
    )
    return HttpResponse(template.render(context, request))


@login_required
def discover_page(request):
    # Get the page number from the URL
    page = int(request.GET.get("page", 1))
    # Get the content type from the URL
    content_type = request.GET.get("content_type", None)

    # Search for TV content if requested
    if content_type == "tv":
        tmdb_results = content_discovery.tv(page, page_multiplier=2)["results"]
        active_tab = STATIC_CONTEXT_VARS["tv_shows"]

    # Search for movie content if requested
    elif content_type == "movie":
        tmdb_results = content_discovery.movies(page, page_multiplier=2)["results"]
        active_tab = STATIC_CONTEXT_VARS["movies"]

    # Search for both content if requested
    else:
        tmdb_results = content_discovery.all(page)["results"]
        active_tab = STATIC_CONTEXT_VARS["combined"]

    template = loader.get_template("viewport/discover.html")

    # Set conreq status for all cards
    set_many_conreq_status(tmdb_results)

    context = generate_context(
        {
            "all_cards": tmdb_results,
            "active_tab": active_tab,
        }
    )
    return HttpResponse(template.render(context, request))


def discover_viewport(content_type):
    # Search for TV content if requested
    if content_type == "tv":
        tmdb_results = content_discovery.tv(page_number=1, page_multiplier=2)["results"]

    # Search for movie content if requested
    elif content_type == "movie":
        tmdb_results = content_discovery.movies(page_number=1, page_multiplier=2)[
            "results"
        ]

    # Search for both content if requested
    else:
        tmdb_results = content_discovery.all(page_number=1)["results"]

    # Set conreq status for all cards
    set_many_conreq_status(tmdb_results)

    context = generate_context(
        {
            "all_cards": tmdb_results,
        }
    )
    return render_to_string("viewport/discover.html", context)