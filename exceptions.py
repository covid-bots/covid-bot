class requestAPIError(Exception):
    """ Raised when trying to get data from the Covid api, but the
    response code is not 200. """
