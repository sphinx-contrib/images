from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import importlib.metadata
import os
import requests
import sphinx
import sys
import uuid

from collections.abc import Iterable
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util import logging, osutil
from typing import Any, Literal, Protocol, TYPE_CHECKING

try:
    from sphinx.util.display import status_iterator
except ImportError:
    # remove when Sphinx < 6.1 is not supported
    from sphinx.util import status_iterator  # type: ignore[no-redef]

if TYPE_CHECKING:
    from sphinx.application import Sphinx as _Sphinx
    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment as _BuildEnvironment
    from sphinx.util.typing import ExtensionMetadata


    class BuildEnvironment(_BuildEnvironment):
        remote_images: dict[str, str]

    class Sphinx(_Sphinx):
        env: BuildEnvironment
        sphinxcontrib_images_backend: type[Backend]


__version__ = '1.0.1'
__author__ = 'Tomasz Czyż <tomaszczyz@gmail.com>'
__license__ = "Apache 2"

logger = logging.getLogger(__name__)

STATICS_DIR_NAME = '_static'

DEFAULT_CONFIG = dict[str, Any](
    backend='LightBox2',
    default_image_width='100%',
    default_image_height='auto',
    default_group=None,
    default_show_title=False,
    download=True,
    requests_kwargs={},
    cache_path='_images',
    override_image_directive=False,
    show_caption=False,
)

def get_entry_points() -> Iterable[importlib.metadata.EntryPoint]:
    group = 'sphinxcontrib.images.backend'
    return (
        importlib.metadata.entry_points(group=group)  # type: ignore[return-value]
        if sys.version_info > (3, 10)
        else importlib.metadata.entry_points()[group]
    )


class Writer(Protocol):
    body: list[str]

    def visit_image(self, node: image_node) -> None:
        ...

    def depart_image(self, node: image_node) -> None:
        ...


class Backend:
    STATIC_FILES: tuple[str, ...] = ()

    def __init__(self, app: Sphinx) -> None:
        self._app = app

    def visit_image_node_fallback(
        self, writer: Writer, node: image_node
    ) -> None:
        writer.visit_image(node)

    def depart_image_node_fallback(
        self, writer: Writer, node: image_node
    ) -> None:
        writer.depart_image(node)


class image_node(nodes.image, nodes.General, nodes.Element):
    pass


def directive_boolean(value: str) -> bool:
    if not value.strip():
        raise ValueError("No argument provided but required")
    if value.lower().strip() in ["yes", "1", 1, "true", "ok"]:
        return True
    elif value.lower().strip() in ['no', '0', 0, 'false', 'none']:
        return False
    else:
        raise ValueError("Please use on of: yes, true, no, false. "
                         f"Do not use `{value}` as boolean.")


def align_option(value: str) -> Literal['left', 'center', 'right']:
    return directives.choice(value, ('left', 'center', 'right'))  # type: ignore[return-value]


class ImageDirective(Directive):
    '''
    Directive which overrides default sphinx directive.
    It's backward compatibile and it's adding more cool stuff.
    '''

    has_content = True
    required_arguments = True

    option_spec = {
        'width': directives.length_or_percentage_or_unitless,
        'height': directives.length_or_unitless,

        'group': directives.unchanged,
        'class': directives.class_option,  # or str?
        'alt': directives.unchanged,
        'download': directive_boolean,
        'title': directives.unchanged,
        'align': align_option,
        'show_caption': directive_boolean,
        'legacy_class': directives.class_option,
    }

    def run(self) -> list[image_node]:
        env = self.state.document.settings.env
        conf = env.app.config.images_config

        #TODO get defaults from config
        group = self.options.get('group',
            conf['default_group'] if conf['default_group'] else uuid.uuid4())
        classes = self.options.get('class', '')
        width = self.options.get('width', conf['default_image_width'])
        height = self.options.get('height', conf['default_image_height'])
        alt = self.options.get('alt', '')
        title = self.options.get('title', '' if conf['default_show_title'] else None)
        align = self.options.get('align', '')
        show_caption = self.options.get('show_caption', False)
        legacy_classes = self.options.get('legacy_class', '')

        #TODO get default from config
        download = self.options.get('download', conf['download'])

        # parse nested content
        #TODO: something is broken here, not parsed as expected
        description = nodes.paragraph()
        content = nodes.paragraph()
        content += [nodes.Text(str(x)) for x in self.content]
        self.state.nested_parse(content, 0, description)

        img = image_node()
        uri = self.arguments[0]

        if self.is_remote(uri):
            img['remote'] = True
            if download:
                local_uri = img['uri'] = os.path.join('_images', hashlib.sha1(uri.encode()).hexdigest())
                img['remote_uri'] = uri
                env.remote_images[uri] = local_uri
                env.images.add_file('', local_uri)
            else:
                img['uri'] = img['remote_uri'] = uri
        else:
            img['uri'] = uri
            img['remote'] = False
            env.images.add_file('', uri)

        img['content'] = description.astext()

        if title is None:
            img['title'] = ''
        elif title:
            img['title'] = title
        else:
            img['title'] = img['content']
            img['content'] = ''

        img['show_caption'] = show_caption
        img['legacy_classes'] = legacy_classes
        img['group'] = group
        img['size'] = (width, height)
        img['classes'] += classes
        img['alt'] = alt
        img['align'] = align
        return [img]

    def is_remote(self, uri: str) -> bool:
        uri = uri.strip()
        env = self.state.document.settings.env
        app_directory = os.path.dirname(os.path.abspath(self.state.document.settings._source))
        if sphinx.__version__.startswith('1.1'):
            app_directory = app_directory.decode('utf-8')

        if uri[0] == '/':
            return False
        if uri[0:7] == 'file://':
            return False
        if os.path.isfile(os.path.join(env.srcdir, uri)):
            return False
        if os.path.isfile(os.path.join(app_directory, uri)):
            return False
        if '://' in uri:
            return True
        raise ValueError(f'Image URI `{uri}` have to be local relative or '
                         'absolute path to image, or remote address.')


def install_backend_static_files(app: Sphinx, env: BuildEnvironment) -> None:
    STATICS_DIR_PATH = os.path.join(app.builder.outdir, STATICS_DIR_NAME)
    dest_path = os.path.join(STATICS_DIR_PATH, 'sphinxcontrib-images',
                             app.sphinxcontrib_images_backend.__class__.__name__)
    files_to_copy = app.sphinxcontrib_images_backend.STATIC_FILES

    for source_file_path in status_iterator(
            files_to_copy,
            'Copying static files for sphinxcontrib-images...',
            'brown', len(files_to_copy)):

        dest_file_path = os.path.join(dest_path, source_file_path)

        if not os.path.exists(os.path.dirname(dest_file_path)):
            osutil.ensuredir(os.path.dirname(dest_file_path))

        assert (
            backend_path := sys.modules[
                app.sphinxcontrib_images_backend.__class__.__module__
            ].__file__
        )
        source_file_path = os.path.join(os.path.dirname(backend_path),
                                        source_file_path)

        osutil.copyfile(source_file_path, dest_file_path)

        if dest_file_path.endswith('.js'):
            app.add_js_file(os.path.relpath(dest_file_path, STATICS_DIR_PATH))
        elif dest_file_path.endswith('.css'):
            app.add_css_file(os.path.relpath(dest_file_path, STATICS_DIR_PATH))


def download_images(app: Sphinx, env: BuildEnvironment) -> None:
    conf = app.config.images_config

    for src in status_iterator(
            env.remote_images,
            'Downloading remote images...',
            'brown',
            len(env.remote_images)):

        dst = os.path.join(env.srcdir, env.remote_images[src])
        if not os.path.isfile(dst):
            logger.info(f'{src!r} -> {dst!r} (downloading)')
            with open(dst, 'wb') as f:
                # TODO: apply reuqests_kwargs
                try:
                    f.write(requests.get(src,
                                        **conf['requests_kwargs']).content)
                except requests.ConnectionError:
                    logger.info(f"Cannot download `{src!r}`")
        else:
            logger.info(f'{src!r} -> {dst!r} (already in cache)')


def update_config(app: Sphinx, config: Config) -> None:
    '''Ensure all config values are defined'''

    merged = copy.deepcopy(DEFAULT_CONFIG)
    merged.update(config.images_config)
    config.images_config = merged

def configure_backend(app: Sphinx) -> None:
    config = app.config.images_config
    osutil.ensuredir(os.path.join(app.env.srcdir, config['cache_path']))

    # html builder
    # self.relfn2path(imguri, docname)

    backend_name_or_callable = config['backend']
    if isinstance(backend_name_or_callable, str):
        try:
            backend = next(
                i for i in get_entry_points() if i.name == backend_name_or_callable
            ).load()
        except StopIteration:
            raise IndexError("Cannot find sphinxcontrib-images backend "
                             f"with name `{backend_name_or_callable!r}`.")
    elif callable(backend_name_or_callable):
        backend = backend_name_or_callable
    else:
        raise TypeError("sphinxcontrib-images backend is configured "
                        "improperly. It has to be a string (name of "
                        "installed backend) or callable which returns "
                        "backend instance but is "
                        f"`{backend_name_or_callable!r}`. Please read "
                        "sphinxcontrib-images documentation for "
                        "more information.")

    try:
        backend = backend(app)
    except TypeError as error:
        logger.info('Cannot instantiate sphinxcontrib-images backend '
                    f'`{config["backend"]}`. Please, select correct backend. '
                    f'Available backends: {", ".join(ep.name for ep in get_entry_points())}.')
        raise SystemExit(1)

    # remember the chosen backend for processing. Env and config cannot be used
    # because sphinx try to make a pickle from it.
    app.sphinxcontrib_images_backend = backend

    logger.info('Initiated sphinxcontrib-images backend: ', nonl=True)
    logger.info(f'`{backend.__class__.__module__}:{backend.__class__.__name__}`')

    def backend_methods(node, output_type):
        def backend_method(f):
            @functools.wraps(f)
            def inner_wrapper(writer, node):
                return f(writer, node)
            return inner_wrapper

        return tuple(
            backend_method(
                getattr(
                    backend,
                    f'{name}_{node.__name__}_{output_type}',
                    getattr(backend, f'{name}_{node.__name__}_fallback'),
                )
            ) for name in ('visit', 'depart')
        )

    # add new node to the stack
    # connect backend processing methods to this node
    app.add_node(image_node,
                 **{output_type: backend_methods(image_node, output_type)
                    for output_type in ('html', 'latex', 'man', 'texinfo',
                                        'text', 'epub')})

    app.add_directive('thumbnail', ImageDirective)
    if config['override_image_directive']:
        app.add_directive('image', ImageDirective)
    app.env.remote_images = {}

def setup(app: Sphinx) -> ExtensionMetadata:
    app.require_sphinx('1.0')
    app.add_config_value('images_config', {}, 'env')
    app.connect('config-inited', update_config)
    app.connect('builder-inited', configure_backend)
    app.connect('env-updated', download_images)
    app.connect('env-updated', install_backend_static_files)

    return {'version': sphinx.__version__, 'parallel_read_safe': True}


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                    choices=['show-backends'])
    args = parser.parse_args(args)
    if args.command == 'show-backends':
        if backends := get_entry_points():
            for backend in backends:
                assert backend.dist
                print(f'- {backend.name} (from package `{backend.dist.name}`)')
        else:
            print('No backends installed')


if __name__ == '__main__':
    main()
