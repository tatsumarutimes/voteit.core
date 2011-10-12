from pyramid.view import view_config
from pyramid.traversal import find_root
from pyramid.url import resource_url
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound

from voteit.core.views.api import APIView
from voteit.core.security import MANAGE_GROUPS, VIEW
from voteit.core.models.security_aware import get_groups_schema
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_cancel

DEFAULT_TEMPLATE = "templates/base_edit.pt"


class EditGroups(object):
    """ View class for adding, editing or deleting dynamic content. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)


    def get_security_appstruct(self, context):
        """ Return the current settings in a structure that is usable in a deform form.
        """
        root = find_root(context)
        users = root['users']
        appstruct = {}
        userids_and_groups = []
        for userid in context._groups:
            user = users[userid]
            userids_and_groups.append({'userid':userid, 'groups':context.get_groups(userid), 'email':user.get_field_value('email')})
        appstruct['userids_and_groups'] = userids_and_groups
        return appstruct

    def get_security_and_invitations_appstruct(self, context):
        """ Return the current settings in a structure that is usable in a deform form,
            including invitations.
        """
        root = find_root(context)
        users = root['users']
        appstruct = {}

        userids_and_groups = []
        for userid in context._groups:
            user = users[userid]
            userids_and_groups.append({'userid':userid, 'groups':context.get_groups(userid), 'email':user.get_field_value('email')})
        appstruct['userids_and_groups'] = userids_and_groups

        #FIXME: this should be readded later
#        invitations_and_groups = []
#        for ticket in context.invite_tickets.values():
#            if ticket.get_workflow_state() != u'closed':
#                invitations_and_groups.append({'email':ticket.email, 'groups':tuple(ticket.roles)})
#        appstruct['invitations_and_groups'] = invitations_and_groups
        return appstruct

    def update_tickets_permissions(self, context, value):
        """ Set tickets permissions from a list of dicts with the following layout:
            {'email':<email>,'groups':<set of groups that the user should have>}.
        """
        for ticket in value:
            context._check_groups(ticket['groups'])
            context.invite_tickets[ticket['email']].roles = tuple(ticket['groups'])

    @view_config(context=ISiteRoot, name="edit_groups", renderer=DEFAULT_TEMPLATE, permission=MANAGE_GROUPS)
    def root_group_form(self):
        schema = get_groups_schema(self.context)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_save, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #Set permissions
            self.context.update_userids_permissions_from_form(appstruct['userids_and_groups'])
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = self.context.get_security_appstruct()
        
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response
        
    @view_config(context=IMeeting, name="participant_permissions", renderer=DEFAULT_TEMPLATE, permission=VIEW)
    def meeting_group_form(self):
        schema = get_groups_schema(self.context)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=('save', 'cancel'))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #Set permissions
            self.context.update_userids_permissions(appstruct['userids_and_groups'])
            #FIXME: this should be readded later
#            self.update_tickets_permissions(self.context, appstruct['invitations_and_groups'])
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)
    
        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = self.get_security_and_invitations_appstruct(self.context)
        
        readonly = not self.api.context_has_permission(MANAGE_GROUPS, self.context)
        self.response['form'] = form.render(appstruct=appstruct, readonly=readonly)
        return self.response
