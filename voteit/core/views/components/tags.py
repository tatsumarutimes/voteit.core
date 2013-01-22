from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.security import effective_principals
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq
from repoze.catalog.query import Any

from voteit.core import VoteITMF as _


@view_action('agenda_item_top', 'tag_stats')
def tag_stats(context, request, *args, **kwargs):
    api = kwargs['api']
    if not api.meeting:
        return ""
    
    workflow_state = ('published', 'unhandled', 'voting', 'approved', 'denied',)
    #if api.meeting.get_field_value('show_retracted', True) or request.GET.get('show_retracted') == '1':
    #    workflow_state = ('published', 'retracted', 'unhandled', 'voting', 'approved', 'denied',)
    
    query = Eq('path', resource_path(context)) & \
            Any('allowed_to_view', effective_principals(request)) & \
            (Eq('content_type', 'Proposal') & Any('workflow_state', workflow_state) | \
             Eq('content_type', 'DiscussionPost'))

    num, docids = api.root.catalog.query(query)
    stats = {}
    for docid in docids:
        entry = api.root.catalog.document_map.get_metadata(docid)
        for tag in entry['tags']:
            if not tag in stats:
                stats[tag] = 1
            else:
                stats[tag] += 1

    stats = sorted([(k, v) for (k, v) in stats.items() if v > 1], key=lambda x: x[1], reverse=True)[:5]
    if not stats:
        return u"" #No reason to continue rendering

    def _make_url(tag):
        query = request.GET.copy()
        query['tag'] = tag
        return request.resource_url(context, query=query)

    response = dict(
        api = api,
        context = context,
        stats = stats,
        make_url = _make_url,
    )
    return render('../templates/snippets/tag_stats.pt', response, request = request)
