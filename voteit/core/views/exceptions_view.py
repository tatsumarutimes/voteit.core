from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.views.api import APIView


class ExceptionView(object):
    """ Exception view, for error messages.
        Note that context might not be related to what caused the error.
    """

    def __init__(self, exception, request):
        self.exception = exception
        self.context = request.context
        self.request = request
        self.api = APIView(request.context, request)
    
    @view_config(context=HTTPForbidden)
    def forbidden_view(self):
        """ I.e. 403. Find first context where user has view permission
            if they're logged in, otherwise redirect to login form.
        """
        self.api.flash_messages.add(self.exception.detail,
                                    type = 'error',
                                    close_button = False)
        # is user logged in
        if self.api.userid:
            obj = self.context
            while obj.__parent__:
                if self.api.context_has_permission(security.VIEW, obj):
                    url = resource_url(obj, self.request)
                    return HTTPFound(location = url)
                obj = obj.__parent__
            return HTTPFound(location = self.request.application_url)
        #Redirect to login
        return HTTPFound(location="%s/@@login?came_from=%s" %(self.request.application_url, self.request.url))

    @view_config(context=HTTPNotFound)
    def not_found_view(self):
        """ I.e. 404.
        """
        err_msg = _(u"404_error_msg",
                    default = u"Can't find anything at '${path}'. Maybe it has been removed?",
                    mapping = {'path': self.exception.detail})
        self.api.flash_messages.add(err_msg,
                                    type = 'error',
                                    close_button = False)
        obj = self.context
        while obj.__parent__:
            if self.api.context_has_permission(security.VIEW, obj):
                url = resource_url(obj, self.request)
                return HTTPFound(location = url)
            obj = obj.__parent__
        return HTTPFound(location = self.request.application_url)