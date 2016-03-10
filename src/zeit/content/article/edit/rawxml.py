from zeit.cms.i18n import MessageFactory as _
import grokcore.component
import lxml.objectify
import zeit.content.article.edit.block
import zeit.content.article.edit.interfaces
import zeit.edit.block


class RawXML(zeit.edit.block.SimpleElement):

    area = zeit.content.article.edit.interfaces.IEditableBody
    grokcore.component.implements(
        zeit.content.article.edit.interfaces.IRawXML)
    type = 'raw'


class Factory(zeit.content.article.edit.block.BlockFactory):

    produces = RawXML
    title = _('Raw XML block')

    def get_xml(self):
        E = lxml.objectify.E
        raw = getattr(E, self.element_type)()
        raw.set('alldevices', 'true')
        raw.append(E.div('\n\n', **{'class': 'article__item x-spacing'}))
        return raw
