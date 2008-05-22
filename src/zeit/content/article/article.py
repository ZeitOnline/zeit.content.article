# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import StringIO

import persistent

import zope.component
import zope.interface
import zope.security.proxy

import zope.app.container.contained

import zeit.cms.connector
import zeit.cms.content.adapter
import zeit.cms.content.dav
import zeit.cms.content.metadata
import zeit.cms.content.interfaces
import zeit.cms.content.property
import zeit.cms.content.util
import zeit.cms.interfaces
import zeit.wysiwyg.html
import zeit.wysiwyg.interfaces

import zeit.content.article.interfaces


ARTICLE_NS = zeit.content.article.interfaces.ARTICLE_NS
ARTICLE_TEMPLATE = """\
<article xmlns:py="http://codespeak.net/lxml/objectify/pytype">
    <head/>
    <body/>
</article>"""


class Article(zeit.cms.content.metadata.CommonMetadata):
    """Article is the main content type in the Zeit CMS."""

    zope.interface.implements(zeit.content.article.interfaces.IArticle)

    default_template = ARTICLE_TEMPLATE

    textLength = zeit.cms.content.dav.DAVProperty(
        zeit.content.article.interfaces.IArticle['textLength'],
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS, 'text-length')
    commentsAllowed = zeit.cms.content.dav.DAVProperty(
        zeit.content.article.interfaces.IArticle['commentsAllowed'],
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS, 'comments')
    boxMostRead = zeit.cms.content.dav.DAVProperty(
        zeit.content.article.interfaces.IArticle['boxMostRead'],
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS, 'mostread')
    pageBreak = zeit.cms.content.dav.DAVProperty(
        zeit.content.article.interfaces.IArticle['pageBreak'],
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS, 'paragraphsperpage')
    dailyNewsletter = zeit.cms.content.dav.DAVProperty(
        zeit.content.article.interfaces.IArticle['dailyNewsletter'],
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS, 'DailyNL')

    zeit.cms.content.dav.mapProperties(
        zeit.content.article.interfaces.IArticle,
        zeit.cms.interfaces.DOCUMENT_SCHEMA_NS,
        ('has_recensions', 'banner', 'artbox_thema'))

    @property
    def paragraphs(self):
        return len(self.xml.body.findall('p'))


articleFactory = zeit.cms.content.adapter.xmlContentFactory(Article)


@zope.interface.implementer(zeit.content.article.interfaces.IArticle)
@zope.component.adapter(zeit.cms.content.interfaces.ITemplate)
def articleFromTemplate(context):
    source = StringIO.StringIO(
        zeit.cms.content.interfaces.IXMLSource(context))
    article = Article(xml_source=source)
    zeit.cms.interfaces.IWebDAVWriteProperties(article).update(
        zeit.cms.interfaces.IWebDAVReadProperties(context))
    return article


resourceFactory = zeit.cms.connector.xmlContentToResourceAdapterFactory(
    'article')
resourceFactory = zope.component.adapter(
    zeit.content.article.interfaces.IArticle)(resourceFactory)


@zope.component.adapter(
    zeit.content.article.interfaces.IArticle,
    zope.lifecycleevent.IObjectModifiedEvent)
def updateTextLengthOnChange(object, event):
    length = zope.security.proxy.removeSecurityProxy(object.xml).body.xpath(
        'string-length()')
    try:
        object.textLength = int(length)
    except zope.security.interfaces.Unauthorized:
        # Ignore when we're not allowed to set it.
        pass


class ArticleHTMLContent(zeit.wysiwyg.html.HTMLContentBase):
    """HTML content of an article."""

    zope.component.adapts(zeit.content.article.interfaces.IArticle)

    def get_tree(self):
        return self.context.xml['body']
