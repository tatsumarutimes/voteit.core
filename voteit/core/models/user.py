from hashlib import sha1
from BTrees.OOBTree import OOBTree
import colander
import deform
from zope.interface import implements
from repoze.folder import unicodify
from pyramid.security import Allow

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.security import ADD_USER


def get_sha_password(password):
    """ Encode a plaintext password to sha1. """
    if isinstance(password, unicode):
        password = password.encode('UTF-8')
    return 'SHA1:' + sha1(password).hexdigest()


class User(BaseContent):
    """ Content type for a user. Usable as a profile page. """
    implements(IUser)
    content_type = 'User'
    allowed_contexts = ('Users',)
    omit_fields_on_edit = () #N/A for this content type
    add_permission = ADD_USER
    
    __acl__ = [(Allow, security.ROLE_ADMIN, security.EDIT),
               (Allow, security.ROLE_OWNER, [security.EDIT, security.CHANGE_PASSWORD])]

    def get_password(self):
        return self.get_field_value('password')
    
    def set_password(self, value):
        """ Encrypt a plaintext password. """
        if not isinstance(value, unicode):
            value = unicodify(value)
        if len(value) < 5:
            raise ValueError("Password must be longer than 4 chars")
        value = get_sha_password(value)
        self.set_field_value('password', value)

    #Override title for users
    def _set_title(self, value):
        #Not used for user content type
        pass
    
    def _get_title(self):
        out = "%s %s" % ( self.get_field_value('first_name'), self.get_field_value('last_name') )
        return out.strip()

    title = property(_get_title, _set_title)


def construct_schema(**kwargs):
    context = kwargs.get('context', None)
    type = kwargs.get('type', None)
    if context is None:
        KeyError("'context' is a required keyword for User schemas. See construct_schema in the user module.")    
    if type is None:
        KeyError("'type' is a required keyword for User schemas. See construct_schema in the user module.")    

    if type == 'login':
        class LoginSchema(colander.Schema):
            userid = colander.SchemaNode(colander.String())
            password = colander.SchemaNode(
                        colander.String(),
                        validator=colander.Length(min=5, max=100),
                        widget=deform.widget.PasswordWidget(size=20),
                        description=_('Enter your password'))
            came_from = colander.SchemaNode(
                        colander.String(),
                        widget = deform.widget.HiddenWidget(),
                        default='/',
                        )
        return LoginSchema()

    if type in ('add', 'registration'):
        class AddUserSchema(colander.Schema):
            userid = colander.SchemaNode(colander.String())
            password = colander.SchemaNode(
                        colander.String(),
                        validator=colander.Length(min=5),
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        description=_(u'Type your password and confirm it'))
            email = colander.SchemaNode(colander.String())
            first_name = colander.SchemaNode(colander.String())
            last_name = colander.SchemaNode(colander.String())
        return AddUserSchema()

    if type == 'edit':
        class EditUserSchema(colander.Schema):
            email = colander.SchemaNode(colander.String())
            first_name = colander.SchemaNode(colander.String())
            last_name = colander.SchemaNode(colander.String())
            biography = colander.SchemaNode(colander.String(),
                        widget = deform.widget.TextAreaWidget(rows=10, cols=60),
                        default = u'')
        return EditUserSchema()

    if type == 'change_password':
        class ChangePasswordSchema(colander.Schema):
            password = colander.SchemaNode(
                        colander.String(),
                        validator=colander.Length(min=5),
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        description=_(u'Type your password and confirm it'))
        return ChangePasswordSchema()

    #No schema found
    raise KeyError("No schema found of type: '%s'" % type)

def includeme(config):
    from voteit.core import register_content_info
    register_content_info(construct_schema, User, registry=config.registry)
