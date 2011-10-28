#from datetime import timedelta

from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from pyramid.exceptions import Forbidden
import colander
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from slugify import slugify
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

#from voteit.core.views.api import APIView
from voteit.core import VoteITMF as _
from voteit.core.security import EDIT
from voteit.core.security import DELETE
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_update
from voteit.core.models.schemas import button_delete
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core import fanstaticlib
from voteit.core.views.api import APIView


DEFAULT_TEMPLATE = "templates/base_edit.pt"


class BaseEdit(object):
    """ View class for adding, editing or deleting dynamic content. """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = {}
        self.response['api'] = self.api = APIView(context, request)
        fanstaticlib.deform.need()
        fanstaticlib.voteit_main_css.need()
        fanstaticlib.voteit_ajax.need()

    @view_config(context=IBaseContent, name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        content_type = self.request.params.get('content_type')
        
        #Permission check
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise Forbidden("You're not allowed to add '%s' in this context." % content_type)
        
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
            
        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            kwargs = {}
            kwargs.update(appstruct)
            if self.api.userid:
                kwargs['creators'] = [self.api.userid]

            obj = createContent(content_type, **kwargs)
            name = self.generate_slug(obj.title)
            self.context[name] = obj
            
            #Only show message if new object isn't discussion or proposal
            if content_type not in ('DiscussionPost', 'Proposal',):
                self.api.flash_messages.add(_(u"Successfully added"))

            url = resource_url(obj, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render add form
        msg = _(u"Add")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    @view_config(context=IBaseContent, name="edit", renderer=DEFAULT_TEMPLATE, permission=EDIT)
    def edit_form(self):
        content_type = self.context.content_type
        schema_name = self.api.get_schema_name(content_type, 'edit')
        schema = createSchema(schema_name).bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_update, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            updated = self.context.set_field_appstruct(appstruct)

            if updated:
                self.api.flash_messages.add(_(u"Successfully updated"))
            else:
                self.api.flash_messages.add(_(u"Nothing updated"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Edit")
        self.api.flash_messages.add(msg, close_button=False)
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response

    @view_config(context=IBaseContent, name="delete", permission=DELETE, renderer=DEFAULT_TEMPLATE)
    def delete_form(self):

        schema = colander.Schema()
        add_csrf_token(self.context, self.request, schema)
        
        form = Form(schema, buttons=(button_delete, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'delete' in post:
            if self.context.content_type == 'SiteRoot' or self.context.content_type == 'Users' or self.context.content_type == 'User':
                raise Exception("Can't delete this content type")

            parent = self.context.__parent__
            del parent[self.context.__name__]

            self.api.flash_messages.add(_(u"Deleted"))

            url = resource_url(parent, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Are you sure you want to delete this item?")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    def generate_slug(self, text, limit=40):
        """ Suggest a name for content that will be added.
            text is a title or similar to be used.
        """
        suggestion = slugify(text[:limit])
        
        #Is the suggested ID already unique?
        if suggestion not in self.context:
            return suggestion
        
        #ID isn't unique, let's try to generate a unique one.
        RETRY = 100
        i = 1
        while i <= RETRY:
            new_s = "%s-%s" % (suggestion, str(i))
            if new_s not in self.context:
                return new_s
            i += 1
        #If no id was found, don't just continue
        raise KeyError("No unique id could be found")
        
    @view_config(context=IWorkflowAware, name="state")
    def state_change(self):
        """ Change workflow state for context.
            Note that if this view is called without the required permission,
            it will raise a WorkflowError exception. This view should
            never be linked to without doing the proper permission checks first.
            (Since the WorkflowError is not the same as Pyramids Forbidden exception,
            which will be handled by the application.)
        """
        state = self.request.params.get('state')
        self.context.set_workflow_state(self.request, state)
        
        url = resource_url(self.context, self.request)
        return HTTPFound(location=url)
