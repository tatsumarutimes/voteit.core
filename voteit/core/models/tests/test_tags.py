import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class UserTagsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.tags import Tags
        return Tags()

    def test_interface(self):
        from voteit.core.models.interfaces import ITags
        obj = self._make_obj()
        self.assertTrue(verifyObject(ITags, obj))

    def test__find_tags(self):
        obj = self._make_obj()
        obj._find_tags('#Quisque #aliquam,#ante in #tincidunt #aliquam. #Risus neque#eleifend #nunc')
        self.assertIn('Quisque', obj._tags)
        self.assertIn('aliquam', obj._tags)
        self.assertIn('ante', obj._tags)
        self.assertIn('tincidunt', obj._tags)
        self.assertIn('aliquam', obj._tags)
        self.assertIn('Risus', obj._tags)
        self.assertIn('nunc', obj._tags)
        self.assertNotIn('eleifend', obj._tags)
        
    def test_add_tag(self):
        obj = self._make_obj()
        obj.add_tag('Quisque')
        self.assertIn('Quisque', obj._tags)
        
    def test_remove_tag(self):
        obj = self._make_obj()
        obj.add_tag('Quisque')
        self.assertIn('Quisque', obj._tags)
        obj.remove_tag('Quisque')
        self.assertNotIn('Quisque', obj._tags)