"""Conreq Content Discovery: Searches TMDB for content."""
from random import shuffle

import tmdbsimple as tmdb
from conreq.core import cache, log
from conreq.core.thread_helper import ReturnThread

# TODO: Obtain these values from the database on init
ANIME_CHECK_FALLBACK = True
LANGUAGE = "en"
FETCH_MULTI_PAGE = 5


class ContentDiscovery:
    """Discovers top, trending, and recommended content using TMDB as the backend.
    >>> Args:
        tmdb_api_key: String containing the TMDB API key.
    """

    def __init__(self, tmdb_api_key):
        # Initialize the TMDB API library
        self.__tmdb_movies = tmdb.Movies()
        self.__tmdb_tv = tmdb.TV()
        self.__search = tmdb.Search()
        self.__discover = tmdb.Discover()
        self.__finder = tmdb.Find()
        self.__genres = tmdb.Genres()
        # TODO: Obtain this value from the database on init
        tmdb.API_KEY = tmdb_api_key

        # Set up result caching dictionaries
        # key = page_number, value = page contents
        self.__popular_movie_cache = {}
        self.__top_movie_cache = {}
        self.__popular_tv_cache = {}
        self.__top_tv_cache = {}
        self.__discover_movie_cache = {}
        self.__discover_tv_cache = {}
        self.__movie_recommendations_cache = {}
        self.__tv_recommendations_cache = {}
        self.__movie_genres_cache = {}
        self.__tv_genres_cache = {}
        self.__movie_similar_cache = {}
        self.__tv_similar_cache = {}
        self.__keyword_id_cache = {}
        self.__movie_by_id_cache = {}
        self.__tv_by_id_cache = {}
        self.__movie_external_id_cache = {}
        self.__tv_external_id_cache = {}
        # key = page_number, value = time when cached
        self.__popular_movie_cache_time = {}
        self.__top_movie_cache_time = {}
        self.__popular_tv_cache_time = {}
        self.__top_tv_cache_time = {}
        self.__discover_movie_cache_time = {}
        self.__discover_tv_cache_time = {}
        self.__movie_recommendations_cache_time = {}
        self.__tv_recommendations_cache_time = {}
        self.__movie_genres_cache_time = {}
        self.__tv_genres_cache_time = {}
        self.__movie_similar_cache_time = {}
        self.__tv_similar_cache_time = {}
        self.__keyword_id_cache_time = {}
        self.__movie_by_id_cache_time = {}
        self.__tv_by_id_cache_time = {}
        self.__movie_external_id_cache_time = {}
        self.__tv_external_id_cache_time = {}

        # Creating a logger (for log files)
        self.__logger = log.get_logger("Content Discovery")
        log.configure(self.__logger, log.WARNING)

    # Exposed class methods
    def all(self, page_number):
        """Get top and popular content from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__all(page_number))

    def tv(self, page_number):
        """Get top and popular TV from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__tv(page_number))

    def movies(self, page_number):
        """Get top and popular TV from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__movies(page_number))

    def popular(self, page_number):
        """Get popular content from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__popular(page_number))

    def top(self, page_number):
        """Get top content from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__top(page_number))

    def popular_movies(self, page_number):
        """Get popular movies from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__popular_movies(page_number))

    def top_movies(self, page_number):
        """Get top movies from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__top_movies(page_number))

    def popular_tv(self, page_number):
        """Get popular TV from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__popular_tv(page_number))

    def top_tv(self, page_number):
        """Get top TV from TMDB.

        Args:
            page_number: An Integer that is the page number to return.
        """
        return self.__shuffle_results(self.__top_tv(page_number))

    def discover(self, content_type, **kwargs):
        """Filter by keywords.

        Args:
            content_type: String containing "movie" or "tv".
            # Additional kwargs #
            keyword: A single String or a List of strings.
            _______: Any other values supported by tmdbsimple discover.movie or discover.tv.
        """
        try:
            if kwargs.__contains__("keyword"):
                # Convert all keywords to IDs
                keyword_ids = self.__keywords_to_ids(kwargs["keyword"])
                if keyword_ids is not None:
                    kwargs["with_keywords"] = keyword_ids

                # Remove keyword strings (invalid parameters)
                kwargs.__delitem__("keyword")

            # Perform a discovery search
            if content_type.lower() == "movie":
                return cache.handler(
                    self.__discover_movie_cache,
                    self.__discover_movie_cache_time,
                    self.__discover.movie,
                    str(kwargs),
                    **kwargs,
                )

            if content_type.lower() == "tv":
                return cache.handler(
                    self.__discover_tv_cache,
                    self.__discover_tv_cache_time,
                    self.__discover.tv,
                    str(kwargs),
                    **kwargs,
                )

            # Content Type was invalid
            log.handler(
                "Invalid content_type " + str(content_type) + " in discover().",
                log.WARNING,
                self.__logger,
            )
            return {}

        except:
            log.handler("Failed to discover!", log.ERROR, self.__logger)
            return {}

    def similar_and_recommended(self, tmdb_id, content_type):
        """Merges the results of similar and recommended.

        Args:
            id: An Integer or String containing the TMDB ID.
            content_type: String containing "movie" or "tv".
        """
        try:
            thread_list = []

            # Get recommended page one
            recommend_page_one = self.__recommended(tmdb_id, content_type, 1)

            # Gather up to 9 additional recommended pages
            for page_number in range(1, recommend_page_one["total_pages"]):
                if page_number <= 5:
                    thread = ReturnThread(
                        target=self.__recommended,
                        args=[tmdb_id, content_type, page_number],
                    )
                    thread.start()
                    thread_list.append(thread)

            # Get similar page one
            similar_page_one = self.__similar(tmdb_id, content_type, 1)

            # Gather up to 9 additional similar pages
            for page_number in range(1, similar_page_one["total_pages"]):
                if page_number <= 5:
                    thread = ReturnThread(
                        target=self.__similar, args=[tmdb_id, content_type, page_number]
                    )
                    thread.start()
                    thread_list.append(thread)

            # Merge results of the first page of similar and recommended
            merged_results = self.__merge_results(recommend_page_one, similar_page_one)

            # Wait for all the threads to complete and merge them in
            for thread in thread_list:
                merged_results = self.__merge_results(merged_results, thread.join())

            # Shuffle and return
            return self.__shuffle_results(merged_results)

        except:
            log.handler(
                "Failed to obtain merged Similar and Recommended!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def get_by_id(self, tmdb_id, content_type):
        """Obtains a movie or series given a TMDB ID.

        Args:
            id: An Integer or String containing the TMDB ID.
            content_type: String containing "movie" or "tv".
        """
        # Searches for content based on TMDB ID
        try:
            # Obtain a movie by ID
            if content_type.lower() == "movie":
                self.__tmdb_movies.id = tmdb_id
                return cache.handler(
                    self.__movie_by_id_cache,
                    self.__movie_by_id_cache_time,
                    self.__tmdb_movies.info,
                    tmdb_id,
                    append_to_response="reviews,keywords,videos,credits,images",
                )

            # Obtain a TV show by ID
            if content_type.lower() == "tv":
                self.__tmdb_tv.id = tmdb_id
                return cache.handler(
                    self.__tv_by_id_cache,
                    self.__tv_by_id_cache_time,
                    self.__tmdb_tv.info,
                    tmdb_id,
                    append_to_response="reviews,keywords,videos,credits,images",
                )

            # Content Type was invalid
            log.handler(
                "Invalid content_type " + str(content_type) + " in get_by_id().",
                log.WARNING,
                self.__logger,
            )
            return {}

        except:
            log.handler(
                "Failed to obtain content by ID!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def get_external_ids(self, tmdb_id, content_type):
        """Gets all external IDs given a TMDB ID.

        Args:
            id: An Integer or String containing the TMDB ID.
            content_type: String containing "movie" or "tv".
        """
        try:
            if content_type.lower() == "movie":
                self.__tmdb_movies.id = tmdb_id
                return cache.handler(
                    self.__movie_external_id_cache,
                    self.__movie_external_id_cache_time,
                    self.__tmdb_movies.external_ids,
                    tmdb_id,
                )

            if content_type.lower() == "tv":
                self.__tmdb_tv.id = tmdb_id
                return cache.handler(
                    self.__tv_external_id_cache,
                    self.__tv_external_id_cache_time,
                    self.__tmdb_tv.external_ids,
                    tmdb_id,
                )
            # Content Type was invalid
            log.handler(
                "Invalid content_type " + str(content_type) + " in get_external_ids().",
                log.WARNING,
                self.__logger,
            )
            return {}

        except:
            log.handler(
                "Failed to obtain external ID!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def get_genres(self, content_type):
        """Gets all external IDs given a TMDB ID.

        Args:
            content_type: String containing "movie" or "tv".
        """
        try:
            if content_type.lower() == "movie":
                return cache.handler(
                    self.__movie_genres_cache,
                    self.__movie_genres_cache_time,
                    self.__genres.movie_list,
                    1,
                )
            if content_type.lower() == "tv":
                return cache.handler(
                    self.__movie_genres_cache,
                    self.__movie_genres_cache_time,
                    self.__genres.tv_list,
                    1,
                )

            # Content Type was invalid
            log.handler(
                "Invalid content_type " + str(content_type) + " in get_genres().",
                log.WARNING,
                self.__logger,
            )
            return {}

        except:
            log.handler(
                "Failed to obtain genres!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def imdb_id_to_tmdb(self, tmdb_id):
        """Converts IMDB ID to TMDB ID.

        Args:
            id: An Integer or String containing the IMDB ID.
        """
        # TODO: Add caching
        try:
            self.__finder.id = tmdb_id
            return self.__finder.info(external_source="imdb_id")

        except:
            log.handler(
                "Failed to obtain imdb ID!",
                log.ERROR,
                self.__logger,
            )
            return None

    def tvdb_id_to_tmdb(self, tmdb_id):
        """Converts TVDB ID to TMDB ID.

        Args:
            id: An Integer or String containing the TMDB ID.
        """
        # TODO: Add caching
        try:
            self.__finder.id = tmdb_id
            return self.__finder.info(external_source="tvdb_id")

        except:
            log.handler(
                "Failed to obtain imdb ID!",
                log.ERROR,
                self.__logger,
            )
            return None

    def is_anime(self, tmdb_id, content_type):
        """Checks if a TMDB ID can be considered Anime.

        Args:
            id: An Integer or String containing the TMDB ID.
            content_type: String containing "movie" or "tv".
        """
        # TODO: Add caching
        try:
            # TV: Obtain the keywords for a specific ID
            if content_type.lower() == "tv":
                self.__tmdb_tv.id = tmdb_id
                api_results = self.__tmdb_tv.keywords()

                # Check if the content contains Keyword: Anime
                if self.__is_key_value_in_results(
                    api_results["results"], "name", "anime"
                ):
                    return True

                # Check if fallback method is enabled
                if ANIME_CHECK_FALLBACK:
                    tv_info = self.__tmdb_tv.info()
                    # Check if genere is Animation and Country is Japan
                    if (
                        self.__is_key_value_in_results(
                            tv_info["genres"], "name", "Animation"
                        )
                        and "JP" in tv_info["origin_country"]
                    ):
                        return True

            # Movies: Obtain the keywords for a specific ID
            elif content_type.lower() == "movie":
                self.__tmdb_movies.id = tmdb_id
                api_results = self.__tmdb_movies.keywords()

                # Check if the content contains Keyword: Anime
                if self.__is_key_value_in_results(
                    api_results["keywords"], "name", "anime"
                ):
                    return True

                # Check if fallback method is enabled
                if ANIME_CHECK_FALLBACK:
                    movie_info = self.__tmdb_movies.info()

                    # Check if genere is Animation and Country is Japan
                    if self.__is_key_value_in_results(
                        movie_info["genres"], "name", "Animation"
                    ) and self.__is_key_value_in_results(
                        movie_info["production_countries"], "iso_3166_1", "JP"
                    ):
                        return True

            # Content Type was invalid
            else:
                log.handler(
                    "Invalid content_type " + str(content_type) + " in is_anime().",
                    log.WARNING,
                    self.__logger,
                )

            log.handler(
                "The " + str(content_type) + " " + str(tmdb_id) + " is not anime.",
                log.INFO,
                self.__logger,
            )

            # None of our methods detected this content as Anime
            return False

        except:
            log.handler(
                "Failed to check if content is anime!",
                log.ERROR,
                self.__logger,
            )
            return False

    # Private Class Methods
    def __all(self, page_number):
        # Merge popular_movies, popular_tv, top_movies, and top_tv results together
        return self.__merge_results(
            self.__popular(page_number), self.__top(page_number)
        )

    def __tv(self, page_number):
        # Merge popular_tv and top_tv results together
        return self.__merge_results(
            self.__popular_tv(page_number), self.__top_tv(page_number)
        )

    def __movies(self, page_number):
        # Merge popular_movies and top_movies results together
        return self.__merge_results(
            self.__popular_movies(page_number), self.__top_movies(page_number)
        )

    def __popular(self, page_number):
        # Merge popular_movies and popular_tv results together
        return self.__merge_results(
            self.__popular_movies(page_number), self.__popular_tv(page_number)
        )

    def __top(self, page_number):
        # Merge top_movies and top_tv results together
        return self.__merge_results(
            self.__top_movies(page_number), self.__top_tv(page_number)
        )

    def __popular_movies(self, page_number):
        # Obtain disovery results through the movie.popular function. Store results in cache.
        return self.__threaded_query(
            self.__popular_movie_cache,
            self.__popular_movie_cache_time,
            self.__tmdb_movies.popular,
            page_number,
        )

    def __top_movies(self, page_number):
        # Obtain disovery results through the movie.top_rated function. Store results in cache.

        return self.__threaded_query(
            self.__top_movie_cache,
            self.__top_movie_cache_time,
            self.__tmdb_movies.top_rated,
            page_number,
        )

    def __popular_tv(self, page_number):
        # Obtain disovery results through the tv.popular function. Store results in cache.

        return self.__threaded_query(
            self.__popular_tv_cache,
            self.__popular_tv_cache_time,
            self.__tmdb_tv.popular,
            page_number,
        )

    def __top_tv(self, page_number):
        # Obtain disovery results through the tv.top_rated function. Store results in cache.

        return self.__threaded_query(
            self.__top_tv_cache,
            self.__top_tv_cache_time,
            self.__tmdb_tv.top_rated,
            page_number,
        )

    def __recommended(self, tmdb_id, content_type, page_number):
        """Obtains recommendations given a TMDB ID.

        Args:
            id: An Integer or String containing the TMDB ID.
            content_type: String containing "movie" or "tv".
            page_number: An Integer that is the page number to return.
        """
        # Performs a recommended search
        try:
            if content_type.lower() == "movie":
                self.__tmdb_movies.id = tmdb_id
                return cache.handler(
                    self.__movie_recommendations_cache,
                    self.__movie_recommendations_cache_time,
                    self.__tmdb_movies.recommendations,
                    str(tmdb_id) + "page" + str(page_number),
                    page=page_number,
                    language=LANGUAGE,
                )

            if content_type.lower() == "tv":
                self.__tmdb_tv.id = tmdb_id
                return cache.handler(
                    self.__tv_recommendations_cache,
                    self.__tv_recommendations_cache_time,
                    self.__tmdb_tv.recommendations,
                    str(tmdb_id) + "page" + str(page_number),
                    page=page_number,
                    language=LANGUAGE,
                )

            # Content Type was invalid
            log.handler(
                "Invalid content_type " + str(content_type) + " in recommend().",
                log.WARNING,
                self.__logger,
            )
            return {}

        except:
            log.handler(
                "Failed to obtain recommendations!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def __similar(self, tmdb_id, content_type, page_number):
        """Obtains similar content given a TMDB ID.

        Args:
            id: An Integer or String containing the TMDB ID.
            content_type: String containing "movie" or "tv".
            page_number: An Integer that is the page number to return.
        """
        # Searches for similar content based on id
        try:
            if content_type.lower() == "movie":
                self.__tmdb_movies.id = tmdb_id
                return cache.handler(
                    self.__movie_similar_cache,
                    self.__movie_similar_cache_time,
                    self.__tmdb_movies.similar_movies,
                    str(tmdb_id) + "page" + str(page_number),
                    page=page_number,
                    language=LANGUAGE,
                )

            if content_type.lower() == "tv":
                self.__tmdb_tv.tmdb_id = tmdb_id
                return cache.handler(
                    self.__tv_similar_cache,
                    self.__tv_similar_cache_time,
                    self.__tmdb_tv.similar,
                    str(tmdb_id) + "page" + str(page_number),
                    page=page_number,
                    language=LANGUAGE,
                )

            # Content Type was invalid
            log.handler(
                "Invalid content_type " + str(content_type) + " in similar().",
                log.WARNING,
                self.__logger,
            )
            return {}

        except:
            log.handler(
                "Failed to obtain similar content!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def __is_key_value_in_results(self, results, key, value):
        # Iterate through each result and check for the key/value pair
        # TODO: Add threading
        try:
            for result in results:
                if result[key] == value:
                    return True

            # The key value pair could not be found in the list of dictionaries
            return False
        except:
            log.handler(
                "Couldn't check for key/value pair in results!",
                log.ERROR,
                self.__logger,
            )
            return False

    def __threaded_query(
        self, cache_dict, cache_time_dict, function, page_number, *args, **kwargs
    ):
        # Thread 5 pages of TMDB queries
        page = page_number * FETCH_MULTI_PAGE
        thread_list = []
        for subtractor in range(0, FETCH_MULTI_PAGE):
            thread = ReturnThread(
                target=cache.handler,
                args=[
                    cache_dict,
                    cache_time_dict,
                    function,
                    page - subtractor,
                ],
                kwargs={"page": page - subtractor, "language": LANGUAGE},
            )
            thread.start()
            thread_list.append(thread)

        # Merge together 5 pages
        merged_results = thread_list[0].join()
        thread_list.remove(thread_list[0])
        for thread in thread_list:
            merged_results = self.__merge_results(merged_results, thread.join())

        return merged_results

    def __keywords_to_ids(self, keywords):
        # Turn a keyword string or a list of keywords into a TMDB keyword ID number
        try:
            keyword_ids = []

            # A list of keywords was given
            if len(keywords) >= 1 and isinstance(keywords, list):
                for keyword in keywords:
                    # Perform a search
                    keyword_search = cache.handler(
                        self.__keyword_id_cache,
                        self.__keyword_id_cache_time,
                        self.__search.keyword,
                        keyword,
                        query=keyword,
                    )["results"]
                    for search_result in keyword_search:
                        # Find an exact match
                        if search_result["name"].lower() == keyword.lower():
                            # Return the keyword ID number
                            keyword_ids.append(search_result["id"])

            # A single keyword was given
            elif len(keywords) >= 1 and isinstance(keywords, str):
                # Perform a search
                keyword_search = cache.handler(
                    self.__keyword_id_cache,
                    self.__keyword_id_cache_time,
                    self.__search.keyword,
                    keywords,
                    query=keywords,
                )["results"]

                for search_result in keyword_search:
                    # Find an exact match
                    if search_result["name"].lower() == keywords.lower():
                        # Return the keyword ID number
                        keyword_ids.append(search_result["id"])

            # User put in values in an improper format
            else:
                log.handler(
                    "Keyword(s) "
                    + str(keywords)
                    + " were provided in an improper format",
                    log.WARNING,
                    self.__logger,
                )
                return None

            # We managed to obtain at least one ID
            if len(keyword_ids) >= 1:
                return keyword_ids

            # We couldn't obtain any IDs
            log.handler(
                "Keyword(s) " + str(keywords) + " not found!",
                log.INFO,
                self.__logger,
            )
            return None

        except:
            log.handler(
                "Failed to obtain keyword!",
                log.ERROR,
                self.__logger,
            )
            return None

    def __merge_results(self, *args):
        # Merge multiple API results into one
        try:
            first_run = True
            merged_results = {}

            for result in args:
                # On the first run, set up the initial dictionary
                if first_run:
                    merged_results = result.copy()
                    first_run = False

                # On subsequent runs, update or merge the values if needed
                else:
                    # Set the total pages to the smallest value
                    if merged_results["total_pages"] > result["total_pages"]:
                        merged_results["total_pages"] = result["total_pages"]

                    # Set the total results to the smallest value
                    if merged_results["total_results"] > result["total_results"]:
                        merged_results["total_results"] = result["total_results"]

                    # Merge the search results
                    merged_results["results"] = (
                        merged_results["results"] + result["results"]
                    )

            return self.__remove_duplicate_results(merged_results)

        except:
            log.handler(
                "Failed to merge results!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def __shuffle_results(self, query):
        # Shuffle API results
        try:
            shuffle(query["results"])
            return query

        except:
            log.handler(
                "Failed to shuffle results!",
                log.ERROR,
                self.__logger,
            )
            return {}

    def __remove_duplicate_results(self, query):
        # Removes duplicates from a dict
        try:
            results = query["results"].copy()

            # Results with no duplicates
            clean_results = []

            # Keys used to determine if duplicates exist
            unique_tv_keys = {}
            unique_movie_keys = {}

            for entry in results:
                # Remove duplicate TV
                if entry.__contains__("name"):
                    if not unique_tv_keys.__contains__(entry["name"]):
                        clean_results.append(entry)
                    unique_tv_keys[entry["name"]] = True

                # Remove duplicate movies
                elif entry.__contains__("title"):
                    if not unique_movie_keys.__contains__(entry["title"]):
                        clean_results.append(entry)
                    unique_movie_keys[entry["title"]] = True

                # Something unexpected happened
                else:
                    log.handler(
                        "While removing duplicates, entry found that did not contain name or title!"
                        + str(entry),
                        log.WARNING,
                        self.__logger,
                    )

            query["results"] = clean_results
            return query
        except:
            log.handler(
                "Failed to remove duplicate results!",
                log.ERROR,
                self.__logger,
            )
            return {}


# Test driver code
if __name__ == "__main__":
    content_discovery = ContentDiscovery("x")

    # print("\n#### Discover All Test ####")
    # pprint(content_discovery.all(1))
    # print("\n#### Discover Top Test ####")
    # pprint(content_discovery.top(1))
    # print("\n#### Discover Top Movies Test ####")
    # pprint(content_discovery.top_movies(1))
    # print("\n#### Discover Top TV Test ####")
    # pprint(content_discovery.top_tv(1))
    # print("\n#### Discover Popular Test ####")
    # pprint(content_discovery.popular(1))
    # print("\n#### Discover Popular Movies Test ####")
    # pprint(content_discovery.popular_movies(1))
    # print("\n#### Discover Popular TV Test ####")
    # pprint(content_discovery.popular_tv(1))
    # print("\n#### TV External ID Test ####")
    # pprint(content_discovery.get_external_ids(2222, "tv"))
    # print("\n#### Movie External ID Test ####")
    # pprint(content_discovery.get_external_ids(2222, "movie"))
    # print("\n#### IMDB to TMDB Test ####")
    # pprint(content_discovery.imdb_id_to_tmdb("tt0266543"))
    # print("\n#### TVDB to TMDB Test ####")
    # pprint(content_discovery.tvdb_id_to_tmdb("276562"))
    # print("\n#### Discover Test ####")
    # pprint(content_discovery.discover("tv", keyword=["anime", "japan"]))
    # print("\n#### Recommend Test ####")
    # pprint(content_discovery.recommend(45923, "tv", 1))
    # print("\n#### Similar Test ####")
    # pprint(content_discovery.similar(45923, "tv", 1))
    # print("\n#### Check if TV is Anime Test ####")
    # pprint(content_discovery.is_anime(63926, "tv"))
    # print("\n#### Check if TV is Anime Test ####")
    # pprint(content_discovery.is_anime(101010, "tv"))
    # print("\n#### Check if Movie is Anime Test ####")
    # pprint(content_discovery.is_anime(592350, "movie"))
    # print("\n#### Check if Movie is Anime Test ####")
    # pprint(content_discovery.is_anime(101010, "movie"))
    # print("\n#### Get TV Genres Test ####")
    # pprint(content_discovery.get_genres("tv"))
    # print("\n#### Get Movie Genres Test ####")
    # pprint(content_discovery.get_genres("movie"))
    # print("\n#### Similar and Recommend Test ####")
    # pprint(content_discovery.similar_and_recommended(45923, "tv"))
