
import os
from sphinxcontrib import images

class LightBox2(images.Backend):
    STATIC_FILES = (
        'lightbox2/dist/images/close.png',
        'lightbox2/dist/images/next.png',
        'lightbox2/dist/images/prev.png',
        'lightbox2/dist/images/loading.gif',
        'lightbox2/dist/js/lightbox-plus-jquery.min.js',
        'lightbox2/dist/js/lightbox-plus-jquery.min.map',
        'lightbox2/dist/css/lightbox.min.css',
        'lightbox2-customize/jquery-noconflict.js',
        'lightbox2-customize/pointer.css'
    )

    def visit_image_node_html(self, writer, node):
        # make links local (for local images only)
        builder = self._app.builder
        if node['uri'] in builder.images:
            node['uri'] = '/'.join([builder.imgpath,
                                    builder.images[node['uri']]])

        if node['show_caption'] is True:
            writer.body.append(
            u'''<figure class="{cls}">
            '''.format(cls=' '.join(node['classes']),))
            if node['legacy_classes']:
                writer.body.append(
                u'''<a class="{legcls}"'''.format(legcls=' '.join(node['legacy_classes']),))
            else:
                writer.body.append(u'''<a ''')
        else:
            writer.body.append(u'''<a class="{cls}"'''.format(cls=' '.join(node['classes']),))

        writer.body.append(
            u'''
               data-lightbox="{group}"
               href="{href}"
               title="{title}"
               data-title="{title}"
               {id}
               >'''.format( group='group-%s' % node['group'] if node['group'] else node['uri'],
                            href=node['uri'],
                            title=node['title'] + node['content'],
                            # Only one id attribute is meaningful
                            id = 'id="' + node['ids'][0] + '"' if len(node['ids'])>0 else ''
                            ))
        writer.body.append(
            '''<img src="{src}"
                     class="{cls}"
                     width="{width}"
                     height="{height}"
                     alt="{alt}"/>
                '''.format(src=node['uri'],
                           cls='align-%s' % node['align'] if node['align'] else '',
                           width=node['size'][0],
                           height=node['size'][1],
                           alt=node['alt'],
                           title=node['title']))


    def depart_image_node_html(self, writer, node):
        writer.body.append('</a>')
        if node['show_caption'] is True:
            writer.body.append(u'''<figcaption>{title}</figcaption>
            '''.format(title=node['title'],))
            writer.body.append('</figure>')
