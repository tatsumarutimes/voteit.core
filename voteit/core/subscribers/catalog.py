from pyramid.traversal import find_interface
from pyramid.events import subscriber
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.catalog import index_object
from voteit.core.models.catalog import reindex_object
from voteit.core.models.catalog import unindex_object


def _update_if_ai_parent(catalog, obj):
    """ Since AIs keep track of count of Poll, Proposal and Discussion objects.
        Only needed for add and remove.
    """
    parent = getattr(obj, '__parent__', None)
    if IAgendaItem.providedBy(parent):
        reindex_object(catalog, parent)

@subscriber([IBaseContent, IObjectAddedEvent])
def object_added(obj, event):
    """ Index a base content object. """
    root = find_interface(obj, ISiteRoot)
    index_object(root.catalog, obj)
    _update_if_ai_parent(root.catalog, obj)

@subscriber([IBaseContent, IObjectUpdatedEvent])
@subscriber([IBaseContent, IWorkflowStateChange])
def object_updated(obj, event):
    """ Reindex a base content object.
        IObjectUpdatedEvent has attributes indexes and metadata to avoid updating catalog if it's not needed.
    """
    root = find_interface(obj, ISiteRoot)
    indexes = set()
    for key in getattr(event, 'indexes', ()):
        if key in root.catalog:
            indexes.add(key)
    metadata = getattr(event, 'metadata', True)
    reindex_object(root.catalog, obj, indexes = indexes, metadata = metadata)

@subscriber([IBaseContent, IObjectWillBeRemovedEvent])
def object_removed(obj, event):
    """ Remove an index for a base content object"""
    root = find_interface(obj, ISiteRoot)
    unindex_object(root.catalog, obj)
    _update_if_ai_parent(root.catalog, obj)
