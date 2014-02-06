# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

from zeit.cms.repository.interfaces import IAutomaticallyRenameable
import gocept.lxml.interfaces
import grokcore.component as grok
import lxml.objectify
import z3c.traverser.interfaces
import zeit.content.article.edit.interfaces
import zeit.content.article.interfaces
import zeit.edit.block
import zeit.edit.container
import zeit.edit.rule
import zope.publisher.interfaces
import zope.schema.interfaces
import zope.security.proxy


editable_body_name = 'editable-body'


class EditableBody(zeit.edit.container.Base,
                   grok.MultiAdapter):

    grok.implements(zeit.content.article.edit.interfaces.IEditableBody)
    grok.provides(zeit.content.article.edit.interfaces.IEditableBody)
    grok.adapts(zeit.content.article.interfaces.IArticle,
                gocept.lxml.interfaces.IObjectified)

    __name__ = editable_body_name

    _find_item = lxml.etree.XPath(
        './/*[@cms:__name__ = $name]',
        namespaces=dict(
            cms='http://namespaces.zeit.de/CMS/cp'))

    def _set_default_key(self, xml_node):
        key = xml_node.get('{http://namespaces.zeit.de/CMS/cp}__name__')
        if not key:
            key = self._generate_block_id()
            xml_node.set('{http://namespaces.zeit.de/CMS/cp}__name__', key)
            self._p_changed = True
        return key

    def _get_keys(self, xml_node):
        # XXX this is much too simple and needs work. and tests.
        result = []
        self.ensure_division()
        for didx, division in enumerate(
            xml_node.xpath('division[@type="page"]'), start=1):
            key = self._set_default_key(division)
            if didx > 1:
                # Skip the first division as it isn't editable
                result.append(key)
            for child in division.iterchildren():
                result.append(self._set_default_key(child))
        return result

    def values(self):
        # We re-implement values() so it works without keys(), since those are
        # not present in the repository and anyway created on demand, which is
        # a Bad Idea(tm) for (concurrent!) read-only purposes (most notably
        # zeit.frontend).

        result = []
        for didx, division in enumerate(
            self.xml.xpath('division[@type="page"]'), start=1):
            if didx > 1:
                result.append(self._get_element_for_node(division))
            for child in division.iterchildren():
                element = self._get_element_for_node(child)
                if element is None:
                    element = self._get_element_for_node(
                        child, zeit.edit.block.UnknownBlock.type)
                result.append(element)
        return result

    def _get_element_type(self, xml_node):
        return xml_node.tag

    def _add(self, item):
        # Add to last division instead of self.xml
        name = item.__name__
        if name:
            if name in self:
                raise zope.container.interfaces.DuplicateIDError(name)
        else:
            name = self._generate_block_id()
            # may migrate so it is guaranteed that there is a division tag:
            self.keys()
        item.__name__ = name
        if zeit.content.article.edit.interfaces.IDivision.providedBy(item):
            self.xml.append(item.xml)
        else:
            self.xml.division[:][-1].append(item.xml)
        self._p_changed = True
        return name

    def _delete(self, key):
        __traceback_info__ = (key,)
        item = self[key]
        assert item is not None
        if zeit.content.article.edit.interfaces.IDivision.providedBy(item):
            # Move contained elements to previous devision
            prev = item.xml.xpath('preceding-sibling::division[1]')[0]
            for child in item.xml.iterchildren():
                prev.append(child)
        item.xml.getparent().remove(item.xml)
        self._p_changed = True
        return item

    def ensure_division(self):
        if self.xml.find('division') is not None:
            return
        i = 0
        division = None
        for node in self.xml.getchildren():
            element = self._get_element_for_node(node)
            if element:
                if i % 7 == 0:
                    division = lxml.objectify.E.division(type='page')
                    self.xml.append(division)
                i += 1
                division.append(node)
        # In case there was neither a division nor any element to put into a
        # division, still create one. This method *ensures* a division exists
        # after it was called
        if division is None:
            self.xml.append(lxml.objectify.E.division(type='page'))
        assert self.xml.find('division') is not None


@grok.adapter(zeit.content.article.interfaces.IArticle)
@grok.implementer(zeit.content.article.edit.interfaces.IEditableBody)
def get_editable_body(article):
    return zope.component.queryMultiAdapter(
        (article,
         zope.security.proxy.removeSecurityProxy(article.xml['body'])),
        zeit.content.article.edit.interfaces.IEditableBody)


class BodyTraverser(object):

    zope.interface.implements(z3c.traverser.interfaces.IPluggableTraverser)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def publishTraverse(self, request, name):
        if name == editable_body_name:
            body = zeit.content.article.edit.interfaces.IEditableBody(
                self.context, None)
            if body is not None:
                return body
        raise zope.publisher.interfaces.NotFound(self.context, name, request)


# Remove all the __name__ thingies on before adding an article to the
# repository
_find_name_attributes = lxml.etree.XPath(
    '//*[@cms:__name__]',
    namespaces=dict(cms='http://namespaces.zeit.de/CMS/cp'))


@grok.subscribe(
    zeit.content.article.interfaces.IArticle,
    zeit.cms.repository.interfaces.IBeforeObjectAddEvent)
def remove_name_attributes(context, event):
    unwrapped = zope.security.proxy.removeSecurityProxy(context)
    for element in _find_name_attributes(unwrapped.xml):
        del element.attrib['{http://namespaces.zeit.de/CMS/cp}__name__']
    lxml.etree.cleanup_namespaces(unwrapped.xml)


class ArticleValidator(zeit.edit.rule.RecursiveValidator, grok.Adapter):

    grok.context(zeit.content.article.interfaces.IArticle)

    @property
    def children(self):
        body = zeit.content.article.edit.interfaces.IEditableBody(self.context)
        return body.values()


@grok.subscribe(
    zeit.content.article.interfaces.IArticle,
    zeit.cms.checkout.interfaces.IValidateCheckinEvent)
def validate_article(context, event):
    # field validation (e.g. zope.schema.Tuple) does type comparisons, which
    # doesn't work with security proxies
    context = zope.security.proxy.removeSecurityProxy(context)
    errors = zope.schema.getValidationErrors(
        zeit.content.article.interfaces.IArticle, context) or []
    if errors:
        errors = [
            (zeit.content.article.interfaces.IArticle[name], error)
            for name, error in errors]
    # XXX using a separate event handler would be cleaner, but we only support
    # retrieving a single error (last_validation_error), so this doesn't work.
    if (IAutomaticallyRenameable(context).renameable
        and not IAutomaticallyRenameable(context).rename_to):
        errors.append(
            (IAutomaticallyRenameable['rename_to'],
             zope.schema.interfaces.RequiredMissing('rename_to')))
    if errors:
        event.veto(errors)
