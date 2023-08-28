from interface.telegram.classes import ActionView, revalidate_search_cache


def revalidate_search_cache_command() -> str:
    try:
        revalidate_search_cache()
    except:
        return "Failed to revalidate search cache"
    return "Search cache has been revalidated"


def init():
    ActionView("settings", [("revalidate_search", revalidate_search_cache_command)])
