from threading import Thread
from time import sleep

from conreq import content_discovery, content_manager, searcher
from conreq.apps.helpers import (
    generate_context,
    preprocess_arr_result,
    preprocess_tmdb_result,
    set_many_conreq_status,
    set_single_conreq_status,
)
from conreq.core.thread_helper import ReturnThread
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.template.loader import render_to_string

# TODO: Obtain this value from the database on init
MAX_SERIES_FETCH_RETRIES = 20


# Create your views here.
@login_required
def more_info(request):
    template = loader.get_template("more_info.html")
    thread_list = []

    # Get the ID from the URL
    tmdb_id = request.GET.get("tmdb_id", None)
    tvdb_id = request.GET.get("tvdb_id", None)

    if tmdb_id is not None:
        content_type = request.GET.get("content_type", None)

        # Get all the basic metadata for a given ID
        tmdb_result = content_discovery.get_by_tmdb_id(tmdb_id, content_type)

        # Get recommended results
        similar_and_recommended_thread = ReturnThread(
            target=content_discovery.similar_and_recommended,
            args=[tmdb_id, content_type],
        )
        similar_and_recommended_thread.start()

        # Checking Conreq status of the current TMDB ID
        thread = Thread(target=set_single_conreq_status, args=[tmdb_result])
        thread.start()
        thread_list.append(thread)

        # Pre-parse data attributes within tmdb_result
        thread = Thread(target=preprocess_tmdb_result, args=[tmdb_result])
        thread.start()
        thread_list.append(thread)

        # Get collection information
        if (
            tmdb_result.__contains__("belongs_to_collection")
            and tmdb_result["belongs_to_collection"] is not None
        ):
            tmdb_collection = True
            tmdb_collection_thread = ReturnThread(
                target=content_discovery.collections,
                args=[tmdb_result["belongs_to_collection"]["id"]],
            )
            tmdb_collection_thread.start()
        else:
            tmdb_collection = None

        # Recommended content
        tmdb_recommended = similar_and_recommended_thread.join()
        if isinstance(tmdb_recommended, list) and len(tmdb_recommended) == 0:
            tmdb_recommended = None

        # Checking Conreq status for all recommended content
        thread = Thread(
            target=set_many_conreq_status, args=[tmdb_recommended["results"]]
        )
        thread.start()
        thread_list.append(thread)

        # Wait for thread computation to complete
        for thread in thread_list:
            thread.join()
        if tmdb_collection is not None:
            tmdb_collection = tmdb_collection_thread.join()

        # Generate context for page rendering
        context = generate_context(
            {
                "content": tmdb_result,
                "recommended": tmdb_recommended,
                "collection": tmdb_collection,
                "content_type": tmdb_result["content_type"],
            }
        )

    elif tvdb_id is not None:
        # Fallback for TVDB
        arr_result = searcher.television(tvdb_id)[0]
        thread_list = []

        # Preprocess results
        thread = Thread(target=preprocess_arr_result, args=[arr_result])
        thread.start()
        thread_list.append(thread)

        # Obtain conreq status
        thread = Thread(target=set_single_conreq_status, args=[arr_result])
        thread.start()
        thread_list.append(thread)

        # Wait for thread computation to complete
        for thread in thread_list:
            thread.join()

        # Generate context for page rendering
        context = generate_context(
            {
                "content": arr_result,
                "content_type": arr_result["contentType"],
            }
        )

    # Render the page
    return HttpResponse(template.render(context, request))


@login_required
def series_modal(tmdb_id=None, tvdb_id=None):
    # Determine the TVDB ID
    if tvdb_id is not None:
        pass

    elif tmdb_id is not None:
        tvdb_id = content_discovery.get_external_ids(tmdb_id, "tv")["tvdb_id"]

    # Check if the show is already within Sonarr's collection
    requested_show = content_manager.get(tvdb_id=tvdb_id)

    # If it doesn't already exists, add then add it
    # TODO: Obtain radarr root and quality profile ID from database
    if requested_show is None:
        sonarr_root = content_manager.sonarr_root_dirs()[0]["path"]
        sonarr_profile_id = content_manager.sonarr_quality_profiles()[0]["id"]

        requested_show = content_manager.add(
            tvdb_id=tvdb_id,
            quality_profile_id=sonarr_profile_id,
            root_dir=sonarr_root,
            series_type="Standard",
        )

    # Keep refreshing until we get the series from Sonarr
    series = content_manager.get(tvdb_id=tvdb_id, obtain_season_info=True)
    if series is None:
        series_fetch_retries = 0
        while series is None:
            if series_fetch_retries > MAX_SERIES_FETCH_RETRIES:
                break
            series_fetch_retries = series_fetch_retries + 1
            sleep(0.5)
            series = content_manager.get(
                tvdb_id=tvdb_id, obtain_season_info=True, force_update_cache=True
            )
            print("Retrying content fetch")

    context = generate_context({"seasons": series["seasons"]})
    return render_to_string("modal/series_selection.html", context)
