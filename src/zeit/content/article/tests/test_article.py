# coding: utf8
from zeit.cms.workflow.interfaces import CAN_PUBLISH_ERROR
from zeit.cms.workflow.interfaces import CAN_PUBLISH_SUCCESS
import lxml.etree
import mock
import zeit.cms.checkout.helper
import zeit.cms.content.interfaces
import zeit.cms.interfaces
import zeit.cms.workflow.interfaces
import zeit.cms.section.interfaces
import zeit.content.article.edit.interfaces
import zeit.content.article.testing
import zeit.magazin.interfaces
import zeit.edit.interfaces
import zeit.edit.rule
import zope.component
import zope.event
import zope.interface
import zope.lifecycleevent
import zeit.cms.content.reference


class WorkflowTest(zeit.content.article.testing.FunctionalTestCase):

    def setUp(self):
        super(WorkflowTest, self).setUp()
        self.article = zeit.cms.interfaces.ICMSContent(
            'http://xml.zeit.de/online/2007/01/Somalia')
        self.info = zeit.cms.workflow.interfaces.IPublishInfo(self.article)

        sm = zope.component.getSiteManager()
        self.orig_validator = sm.adapters.lookup(
            (zeit.content.article.interfaces.IArticle,),
            zeit.edit.interfaces.IValidator)

        self.validator = mock.Mock()
        zope.component.provideAdapter(
            self.validator,
            adapts=(zeit.content.article.interfaces.IArticle,),
            provides=zeit.edit.interfaces.IValidator)

    def tearDown(self):
        zope.component.getSiteManager().unregisterAdapter(
            required=(zeit.content.article.interfaces.IArticle,),
            provided=zeit.edit.interfaces.IValidator)
        zope.component.provideAdapter(
            self.orig_validator,
            adapts=(zeit.content.article.interfaces.IArticle,),
            provides=zeit.edit.interfaces.IValidator)
        super(WorkflowTest, self).tearDown()

    def test_not_urgent_cannot_publish(self):
        self.assertFalse(self.info.urgent)
        self.assertEqual(CAN_PUBLISH_ERROR, self.info.can_publish())
        self.assertFalse(self.validator.called)

    def test_validation_passes_can_publish(self):
        self.info.urgent = True
        self.validator().status = None
        self.assertEqual(CAN_PUBLISH_SUCCESS, self.info.can_publish())
        self.validator.assert_called_with(self.article)

    def test_validation_fails_cannot_publish(self):
        self.info.urgent = True
        self.validator().status = zeit.edit.rule.ERROR
        self.validator().messages = []
        self.assertEqual(CAN_PUBLISH_ERROR, self.info.can_publish())
        self.validator.assert_called_with(self.article)


class DivisionTest(zeit.content.article.testing.FunctionalTestCase):

    # See bug #9495

    def get_article_with_paras(self):
        article = self.get_article()
        factory = self.get_factory(article, 'p')
        for _ in range(10):
            factory()
        return article

    def test_article_should_not_mangle_divisions_on_create(self):
        article = self.get_article_with_paras()
        self.assertEqual(1, len(article.xml.body.findall('division')))

    def test_article_should_not_mangle_divisions_on_add_to_repository(self):
        article = self.get_article_with_paras()
        self.repository['article'] = article
        self.assertEqual(
            1, len(self.repository['article'].xml.body.findall('division')))

    def test_article_should_not_mangle_divisions_on_checkin(self):
        from zeit.cms.checkout.helper import checked_out
        article = self.get_article_with_paras()
        self.repository['article'] = article
        with checked_out(self.repository['article']):
            pass
        self.assertEqual(
            1, len(self.repository['article'].xml.body.findall('division')))

    def test_article_without_division_should_get_them_on_checkin(self):
        from zeit.cms.checkout.helper import checked_out
        article = self.get_article_with_paras()
        # mangle the xml
        for p in article.xml.body.division.getchildren():
            article.xml.body.append(p)
        article.xml.body.remove(article.xml.body.division)
        self.repository['article'] = article
        with checked_out(self.repository['article']):
            pass
        self.assertEqual(
            2, len(self.repository['article'].xml.body.findall('division')))


class MainImageTest(zeit.content.article.testing.FunctionalTestCase):

    def test_main_image_is_none_if_first_body_is_empty(self):
        article = self.get_article()
        self.assertEqual(None, article.main_image)

    def test_main_image_is_none_if_first_block_is_not_an_image(self):
        article = self.get_article()
        self.get_factory(article, 'p')()
        self.assertEqual(None, article.main_image)

    def test_main_image_is_none_if_first_block_is_an_empty_image(self):
        article = self.get_article()
        self.get_factory(article, 'image')()
        self.assertEqual(None, article.main_image)

    def test_main_image_is_returned_if_first_block_contains_one(self):
        article = self.get_article()
        block = self.get_factory(article, 'image')()
        image = zeit.cms.interfaces.ICMSContent(
            'http://xml.zeit.de/2006/DSC00109_2.JPG')
        block.references = block.references.create(image)
        self.assertEqual(image, article.main_image.target)

    def test_setting_main_image_is_reflected_inside_body(self):
        article = self.get_article()
        block = self.get_factory(article, 'image')()
        image = zeit.cms.interfaces.ICMSContent(
            'http://xml.zeit.de/2006/DSC00109_2.JPG')
        article.main_image = article.main_image.create(image)
        body = zeit.content.article.edit.interfaces.IEditableBody(article)
        block = body.values()[0]
        self.assertEqual(image, block.references.target)
        self.assertFalse(block.is_empty)

    def test_setting_main_image_works_if_body_does_not_start_with_image(self):
        article = self.get_article()
        image = zeit.cms.interfaces.ICMSContent(
            'http://xml.zeit.de/2006/DSC00109_2.JPG')
        article.main_image = article.main_image.create(image)
        body = zeit.content.article.edit.interfaces.IEditableBody(article)
        block = body.values()[0]
        self.assertEqual(image, block.references.target)


class NormalizeQuotes(zeit.content.article.testing.FunctionalTestCase):

    def test_normalize_body(self):
        article = self.get_article()
        p = self.get_factory(article, 'p')()
        p.text = '“up” and „down‟ and «around»'
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(
                self.repository['article']) as co:
            body = zeit.content.article.edit.interfaces.IEditableBody(co)
            block = body.values()[0]
            self.assertEqual('"up" and "down" and "around"', block.text)

    def test_normalize_teaser(self):
        article = self.get_article()
        article.teaserTitle = u'“up” and „down‟ and «around»'
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(
                self.repository['article']) as co:
            self.assertEqual('"up" and "down" and "around"', co.teaserTitle)


class LayoutHeaderByArticleTemplate(
        zeit.content.article.testing.FunctionalTestCase):

    def test_header_layout_should_determine_header_module_visibility(self):
        article = self.get_article()
        article.template = u'column'
        article.header_layout = u'default'
        source = zeit.content.article.source.ArticleTemplateSource().factory
        self.assertTrue(source.allow_header_module(article))


class DefaultTemplateByContentType(
        zeit.content.article.testing.FunctionalTestCase):

    def test_config_should_define_default_template_for_context(self):
        article = self.get_article()
        source = zeit.content.article.source.ArticleTemplateSource().factory

        has_default = source._provides_default(
            article,
            ['zeit.cms.section.interfaces.IZONContent'])
        self.assertFalse(has_default)

        zope.interface.alsoProvides(article,
                                    zeit.cms.section.interfaces.IZONContent)
        has_default = source._provides_default(
            article,
            ['zeit.cms.section.interfaces.IZONContent'])
        self.assertTrue(has_default)

        article = self.get_article()
        zope.interface.alsoProvides(article,
                                    zeit.magazin.interfaces.IZMOContent)
        has_default = source._provides_default(
            article,
            ['zeit.cms.section.interfaces.IZONContent',
             'zeit.magazin.interfaces.IZMOContent'])
        self.assertTrue(has_default)

    def test_config_should_define_generic_default_for_context(self):
        source = zeit.content.article.source.ArticleTemplateSource().factory
        self.assertEquals(
            ('article', 'inside'),
            source._get_generic_default())

    def test_config_should_provide_defaults(self):
        article = self.get_article()
        source = zeit.content.article.source.ArticleTemplateSource().factory
        zope.interface.alsoProvides(article,
                                    zeit.cms.section.interfaces.IZONContent)
        self.assertEquals(
            ('article', 'default'),
            source.get_default_template(article))

        article = self.get_article()
        source = zeit.content.article.source.ArticleTemplateSource().factory
        zope.interface.alsoProvides(article,
                                    zeit.magazin.interfaces.IZMOContent)
        self.assertEquals(
            ('short', ''),
            source.get_default_template(article))

        article = self.get_article()
        self.assertEquals(
            ('article', 'inside'),
            source.get_default_template(article))

    def test_article_should_have_default_template_on_checkout(self):
        article = self.get_article()
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(self.repository['article']):
            pass
        self.assertEquals('article', self.repository['article'].template)
        self.assertEquals('default', self.repository['article'].header_layout)

    def test_checkout_should_not_change_template_if_already_set(self):
        article = self.get_article()
        article.template = u'column'
        article.header_layout = u'heiter'
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(self.repository['article']):
            pass
        self.assertEquals('column', self.repository['article'].template)
        self.assertEquals('heiter', self.repository['article'].header_layout)

    def test_checkout_should_assign_default_if_current_value_invalid(self):
        article = self.get_article()
        article.template = u'nonexistent'
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(self.repository['article']):
            pass
        self.assertEquals('article', self.repository['article'].template)

    def test_article_should_have_default_variant_name_on_checkout(self):
        article = self.get_article()
        article._create_image_block_in_front()
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(self.repository['article']):
            pass
        self.assertEquals(
            'original', self.repository['article'].main_image_variant_name)

    def test_checkout_should_not_change_variant_name_if_already_set(self):
        article = self.get_article()
        article._create_image_block_in_front()
        article.main_image_variant_name = 'wide'
        self.repository['article'] = article
        with zeit.cms.checkout.helper.checked_out(self.repository['article']):
            pass
        self.assertEquals(
            'wide', self.repository['article'].main_image_variant_name)


class AccessRestrictsAMPandFBIA(
    zeit.content.article.testing.FunctionalTestCase):

    def setUp(self):
        super(AccessRestrictsAMPandFBIA, self).setUp()
        self.repository['article'] = self.get_article()
        self.article = self.repository['article']

    def notify_modified(self, article, field='access'):
        zope.event.notify(zope.lifecycleevent.ObjectModifiedEvent(
            article, zope.lifecycleevent.Attributes(
                zeit.cms.content.interfaces.ICommonMetadata, field)))

    def test_setting_access_to_abo_or_registration_disables_amp_and_fbia(self):
        with zeit.cms.checkout.helper.checked_out(self.article) as article:
            article.is_amp = True
            article.is_instant_article = True
            article.access = u'abo'
            self.notify_modified(article)
            self.assertEqual(False, article.is_amp)
            self.assertEqual(False, article.is_instant_article)

            article.is_amp = True
            article.is_instant_article = True
            article.access = u'registration'
            self.notify_modified(article)
            self.assertEqual(False, article.is_amp)
            self.assertEqual(False, article.is_instant_article)

    def test_setting_access_to_free_does_not_change_is_amp_and_fbia(self):
        with zeit.cms.checkout.helper.checked_out(self.article) as article:
            article.is_amp = True
            article.is_instant_article = True
            article.access = u'free'
            self.notify_modified(article)
            self.assertEqual(True, article.is_amp)
            self.assertEqual(True, article.is_instant_article)

    def test_do_not_change_is_amp_if_access_is_missing(self):
        """For bw-compat old articles without access are treated as free."""
        with zeit.cms.checkout.helper.checked_out(self.article) as article:
            article.is_amp = True
            article.is_instant_article = True
            article.access = None
            self.notify_modified(article)
            self.assertEqual(True, article.is_amp)
            self.assertEqual(True, article.is_instant_article)

    def test_only_change_is_amp_if_access_was_changed(self):
        with zeit.cms.checkout.helper.checked_out(self.article) as article:
            article.access = u'abo'
            article.is_amp = True
            article.is_instant_article = True
            article.year = 2016
            self.notify_modified(article, 'year')
            self.assertEqual(True, article.is_amp)
            self.assertEqual(True, article.is_instant_article)


class ArticleXMLReferenceUpdate(
        zeit.content.article.testing.FunctionalTestCase):

    def test_writes_genre_as_attribute(self):
        self.repository['article'] = article = self.get_article()
        with zeit.cms.checkout.helper.checked_out(article) as co:
            co.genre = u'nachricht'

        reference = zope.component.queryAdapter(
            article, zeit.cms.content.interfaces.IXMLReference, name='related')
        self.assertIn(
            'genre="nachricht"',
            lxml.etree.tostring(reference, pretty_print=True))


class ArticleElementReferencesTest(
        zeit.content.article.testing.FunctionalTestCase):

    def setUp(self):
        super(ArticleElementReferencesTest, self).setUp()
        self.article = self.get_article()

    def create_empty_portraitbox_reference(self):
        from zeit.content.article.edit.body import EditableBody
        body = EditableBody(self.article, self.article.xml.body)
        portraitbox_reference = body.create_item('portraitbox', 1)
        portraitbox_reference._validate = mock.Mock()
        return portraitbox_reference

    def test_articles_element_references_iterates_over_references(self):
        from zeit.content.portraitbox.portraitbox import Portraitbox
        pbox = Portraitbox()
        self.repository['pbox'] = pbox
        ref = self.create_empty_portraitbox_reference()
        ref.references = pbox
        self.assertEqual([pbox], list(zeit.edit.interfaces.IElementReferences(
            self.article)))

    def test_articles_element_references_is_empty_if_no_references_are_set(self):
        self.assertEqual([], list(zeit.edit.interfaces.IElementReferences(
            self.article)))

    def test_articles_element_references_is_empty_if_empty_reference_is_set(
            self):
        self.create_empty_portraitbox_reference()
        self.assertEqual([], list(zeit.edit.interfaces.IElementReferences(
            self.article)))
