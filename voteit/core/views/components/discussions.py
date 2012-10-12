# -*- coding:utf-8 -*-

from betahaus.viewcomponent import view_action
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from pyramid.traversal import find_interface
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import DELETE
from voteit.core.helpers import truncate


@view_action('discussions', 'listing')
def discussions_listing(context, request, va, **kw):
    """ Get discussions for a specific context """
    api = kw['api']

    def _show_delete(brain):
        #Do more expensive checks last!
        if not api.userid in brain['creators']:
            return
        obj = find_resource(api.root, brain['path'])
        return api.context_has_permission(DELETE, obj)

    path = resource_path(context)
    
    tag = request.GET.get('tag', None)
    
    query = dict(path = path,
                 content_type='DiscussionPost')
    
    query['sort_index'] = 'created'
    query['reverse'] = True
    
    total_count = api.search_catalog(**query)[0]
    
    if tag:
        query['tags'] = tag

    if request.GET.get('discussions', '') == 'all' or tag:
        limit = 0
    else:
        unread_count = api.search_catalog(unread = api.userid, **query)[0]
        limit = 5
        if unread_count > limit:
            limit = unread_count

    
    #Returns tuple of (item count, iterator with docids)
    count = api.search_catalog(**query)[0]

    #New query with only limited number of results
    if limit:
        query['limit'] = limit
    docids = api.search_catalog(**query)[1]
    get_metadata = api.root.catalog.document_map.get_metadata
    results = []
    for docid in docids:
        #Insert the resolved docid first, since we need to reverse order again.
        results.insert(0, get_metadata(docid))
        
    #Get truncate length from meeting
    meeting = find_interface(context, IMeeting)
    #FIXME: needs a way to set default value on this on creation of meeting
    truncate_length = meeting.get_field_value('truncate_discussion_length', 240)
    
    # build query string and remove discussions=all
    more_query = request.GET.copy()
    if 'discussions' in more_query: 
        del more_query['discussions']
    
    # build query string and remove tag=
    clear_tag_query = request.GET.copy()
    if 'tag' in clear_tag_query:
        del clear_tag_query['tag'] 
        
    response = {}
    response['clear_tag_url'] = api.request.resource_url(context, query=clear_tag_query)
    response['more_url_all'] = api.request.resource_url(context, 'discussions', query=dict(more_query.items()+{'discussions': 'all'}.items()))
    response['more_url_normal'] = api.request.resource_url(context, 'discussions', query=more_query)
    response['discussions'] = tuple(results)
    if limit and limit < count:
        response['over_limit'] = count - limit
    else:
        response['over_limit'] = 0
    response['hidden_count'] = total_count - count
    response['limit'] = limit
    response['api'] = api
    response['show_delete'] = _show_delete
    response['truncate'] = truncate 
    response['truncate_length'] = truncate_length
    return render('../templates/discussions.pt', response, request = request)
