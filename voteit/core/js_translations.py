from voteit.core import VoteITMF as _ 
from voteit.core.models.interfaces import IJSUtil


def includeme(config):
    """ Add default js translations to system.
        Note that the msgids here are used by javascript - don't change them
        unless you know what you're doings!
    """
    util = config.registry.getUtility(IJSUtil)
    util.add_translations(
        yes = _(u"Yes"),
        no = _(u"No"),
        close = _(u"Close"),
        confirm_title = _(u"Please confirm"),
        confirm_state = _(u"Are you sure you want to change the state?"),
        confirm_retract = _(u"Are you sure you want to retract this proposal?"),
        user_info = _(u"About..."),
        more_tag_list = _(u"More..."),
        loading = _(u"Loading..."),
        help_contact = _(u"Help &amp; Contact"),
        poll = _(u"Poll"),
        voting_error_msg = _(u"An error occurred while voting, please try again."),
        voting_timeout_msg = _(u"Server didn't respond, many participants may be voteing right now, please try again."),
        waiting = _(u"Waiting..."),
    )
