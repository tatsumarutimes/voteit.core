# -*- coding:utf-8 -*-

import re

from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root
from pyramid.traversal import find_interface
from pyramid.url import resource_url
from webhelpers.html import HTML
from webhelpers.html.render import sanitize
from webhelpers.html.converters import nl2br
from betahaus.pyracont import generate_slug #For b/c, please keep this until cleared!

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.tags import TAG_PATTERN


ajax_options = """
{success: voteit_deform_success,
}
"""

AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]+)', flags=re.UNICODE)

def at_userid_link(text, obj, request=None):
    """ Transform @userid to a link.
    """
    users = find_root(obj).users
    meeting = find_interface(obj, IMeeting)
    assert meeting
    if not request:
        request = get_current_request()

    def handle_match(matchobj):
        # The pattern contains a space so we only find usernames that 
        # has a whitespace in front, we save the spaced so we can but 
        # it back after the transformation
        space, userid = matchobj.group(1, 2)
        #Force lowercase userid
        userid = userid.lower()
        if userid in users: 
            user = users[userid]
    
            tag = {}
            tag['href'] = request.resource_url(meeting, '_userinfo', query={'userid': userid}).replace(request.application_url, '')
            tag['title'] = user.title
            tag['class'] = "inlineinfo"
            return space + HTML.a('@%s' % userid, **tag)
        else:
            return space + '@' + userid

    return re.sub(AT_PATTERN, handle_match, text)


def tags2links(text, context, request):
    """ Transform #tag to a link.
    """
    ai = find_interface(context, IAgendaItem)
    assert ai

    def handle_match(matchobj):
        pre, tag, post = matchobj.group(1, 2, 3)
        link = {'href': request.resource_url(ai, '', query={'tag': tag}).replace(request.application_url, ''),
                'class': "tag",}
        
        return pre + HTML.a('#%s' % tag, **link) + post

    return re.sub(TAG_PATTERN, handle_match, text)

def strip_and_truncate(text, limit=200):
    try:
        text = sanitize(text)
    except Exception, e:
        #FIXME: Logg unrecoverable error
        #This is a bad exception that should never happen, if we translate it it will be hard to search in the source code
        return u"Unrecoverable error: could not truncate text"
    if len(text) > limit:
        text = u"%s<...>" % nl2br(text[:limit])
    return nl2br(text)

def truncate(text, length=240):
    ''' returns text truncated to closest withspace after 
        length and a flag if it was truncated 
    '''

    # if text is shorter then lenght return full text 
    if not length or len(text) <= length:
        return (text, False)
    
    # find first whitespace after length
    m = re.search("\s+", text[length:]) 
    
    # no whitespace after length, return full text
    if not m:
        return (text, False)
    
    # cut text at the first whitespace after lenght
    trunc = u"%s …" % text[:length+m.start()]

    return (trunc, text != trunc)