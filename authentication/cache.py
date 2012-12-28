class CachePoint:
    def __init__(self):
        self.has_value = False
        self.value = None
        
    def __repr__(self):
        return '%s %s' % (self.has_value, self.value)

def set_cache_value(cache, params, value):
    if len(params) == 1:
        cache[params[0]].has_value = True
        cache[params[0]].value = value
    else:
        if params[0] not in cache:
            cache[params[0]] = {}
        return set_cache_value(cache[params[0]], params[1:], value)
    
def get_cache_point(cache, params):
    if len(params) == 1:
        if params[0] not in cache:
            cache[params[0]] = CachePoint()
        return cache[params[0]]
    else:
        if params[0] not in cache:
            cache[params[0]] = {}
        return get_cache_point(cache[params[0]], params[1:])
    
def get_from_cache(function, params):
    from curia import get_current_request
    cache = get_current_request().access_cache
    point = get_cache_point(cache, (function.func_name,)+params)
    if not point.has_value:
        value = function(*params)
        set_cache_value(cache, (function.func_name,)+params, value)
        
    return point.value
    
# note that this simple caching system does not support keyword arguments    
def cache_access(function):
    def cached_function(*args):
        f = get_from_cache(function, args)
        return f
    return cached_function