import html

from sphinxcontrib import images


def _a(value: str) -> str:
    return html.escape(value, quote=True)


def _h(value: str) -> str:
    return html.escape(value)


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

    def visit_image_node_html(
        self, writer: images.Writer, node: images.image_node
    ) -> None:
        # make links local (for local images only)
        builder = self._app.builder
        if node['uri'] in builder.images:
            node['uri'] = '/'.join([builder.imgpath, builder.images[node['uri']]])

        # add wrapping optional figure tag and then anchor tag
        if node['show_caption']:
            writer.body.append(f'<figure class="{_a(" ".join(node["classes"]))}">')
            writer.body.append('<a ')
            if node['legacy_classes']:
                writer.body.append(f'class="{_a(" ".join(node["legacy_classes"]))}" ')
        else:
            writer.body.append(f'<a class="{_a(" ".join(node["classes"]))}" ')

        # add anchor attributes
        link_title = f'{node["title"]}{node["content"]}'
        for attr, value in (
            ('data-lightbox', f'group-{node["group"]}' if node['group'] else node['uri']),
            ('href', node['uri']),
            ('title', link_title),
            ('data-title', link_title),
            # Only one id attribute is meaningful
            *([('id', node['ids'][0])] if node['ids'] else ()),
        ):
            writer.body.append(f'{attr}="{_a(value)}" ')

        # finish anchor tag and start image tag
        writer.body.append(f'><img ')

        # add image attributes
        for attr, value in (
            ('src', node["uri"]),
            ('width', node['size'][0]),
            ('height', node['size'][1]),
            ('alt', node['alt']),
            ('title', node['title']),
            *([('class', f'align-{node["align"]}')] if node['align'] else ()),
        ):
            writer.body.append(f'{attr}="{_a(value)}" ')

        writer.body.append(f'/>')


    def depart_image_node_html(
        self, writer: images.Writer, node: images.image_node
    ) -> None:
        writer.body.append('</a>')
        if node['show_caption']:
            writer.body.append(f'<figcaption>{_h(node["title"])}</figcaption>')
            writer.body.append('</figure>')
