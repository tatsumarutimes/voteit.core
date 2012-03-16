from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.traversal import find_resource
from pyramid.traversal import resource_path
from pyramid.security import Everyone
from pyramid.security import effective_principals
from repoze.catalog.query import Eq
from repoze.catalog.query import Any
from repoze.catalog.query import Contains
from repoze.catalog.query import Name
from betahaus.pyracont.factories import createSchema
from webhelpers.html.converters import nl2br
from webhelpers.html.render import sanitize

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import button_search
from voteit.core.models.schemas import add_csrf_token
from voteit.core.security import VIEW
from voteit.core import VoteITMF as _


SEARCH_VIEW_QUERY = Eq('path', Name('path')) \
    & Contains('searchable_text', Name('searchable_text')) \
    & Any('content_type', ('DiscussionPost', 'Proposal', )) \
    & Any('allowed_to_view', Name('allowed_to_view'))


def _strip_and_truncate(text, limit=200):
    text = sanitize(text)
    if len(text) > limit:
        text = u"%s<...>" % nl2br(text[:limit])
    return nl2br(text)


class SearchView(BaseView):
    """ Handle incoming search query and display result. """

    @view_config(context=IMeeting, name="search", renderer="templates/search.pt", permission = VIEW)
    def search(self):
        schema = createSchema('SearchSchema').bind(context = self.context, request = self.request)
        add_csrf_token(self.context, self.request, schema)        
        form = Form(schema, buttons=(button_search,))
        self.api.register_form_resources(form)
        appstruct = {}
        self.response['results'] = []

        def _results_ts(count):
            return self.api.pluralize(_(u"item"),
                                      _(u"items"),
                                      count)

        post = self.request.POST
        if 'search' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['search_form'] = e.render()
                return self.response

            #Preform the actual search
            query = {}
            if appstruct['query']:
                query['searchable_text'] = appstruct['query']
            query['path'] = resource_path(self.api.meeting)
            if self.api.userid:
                query['allowed_to_view'] = effective_principals(self.request)
            else:
                query['allowed_to_view'] = [Everyone]

            cat_query = self.api.root.catalog.query
            get_metadata = self.api.root.catalog.document_map.get_metadata
            num, results = cat_query(SEARCH_VIEW_QUERY, names = query)
            self.response['results'] = [get_metadata(x) for x in results]

        self.response['search_form'] = form.render(appstruct = appstruct)
        self.response['query_data'] = appstruct
        self.response['results_ts'] = _results_ts
        self.response['results_count'] = len(self.response['results'])
        self.response['strip_truncate'] = _strip_and_truncate
        return self.response
