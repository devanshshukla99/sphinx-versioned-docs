"""Interface with Sphinx."""

import pathlib
import datetime
import logging
import multiprocessing
import os
import typer
import sys
from shutil import copyfile, rmtree

from loguru import logger as log
from sphinx import application, locale
from sphinx.cmd.build import build_main, make_main
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.config import Config as SphinxConfig
from sphinx.errors import SphinxError
from sphinx.jinja2glue import SphinxFileSystemLoader

from sphinxcontrib.versioning import __version__
from sphinxcontrib.versioning.lib import HandledError, TempDir
from sphinx.util.fileutil import copy_asset_file

SC_VERSIONING_VERSIONS = list()  # Updated after forking.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "_static")
CLICK_COMMAND = None


class Config(object):
    """The global configuration and state of the running program."""

    def __init__(self):
        """Constructor."""
        self._already_set = set()
        self._program_state = dict()

        # Booleans.
        self.banner_greatest_tag = False
        self.banner_recent_tag = False
        self.greatest_tag = False
        self.invert = False
        self.no_colors = False
        self.no_local_conf = False
        self.recent_tag = False
        self.show_banner = False

        # Strings.
        self.banner_main_ref = "master"
        self.chdir = None
        self.git_root = None
        self.local_conf = None
        self.priority = None
        self.root_ref = "master"

        # Tuples.
        self.overflow = tuple()
        self.sort = tuple()
        self.whitelist_branches = tuple()
        self.whitelist_tags = tuple()

        # Integers.
        self.verbose = 0

        # Custom.
        self.pdf_file = None  # Name of the pdf

    def __contains__(self, item):
        """Implement 'key in Config'.

        :param str item: Key to search for.

        :return: If item in self._program_state.
        :rtype: bool
        """
        return item in self._program_state

    def __iter__(self):
        """Yield names and current values of attributes that can be set from Sphinx config files."""
        for name in (n for n in dir(self) if not n.startswith("_") and not callable(getattr(self, n))):
            yield name, getattr(self, name)

    def __repr__(self):
        """Class representation."""
        attributes = ("_program_state", "verbose", "root_ref", "overflow")
        key_value_attrs = ", ".join("{}={}".format(a, repr(getattr(self, a))) for a in attributes)
        return "<{}.{} {}>".format(self.__class__.__module__, self.__class__.__name__, key_value_attrs)

    def __setitem__(self, key, value):
        """Implement Config[key] = value, updates self._program_state.

        :param str key: Key to set in self._program_state.
        :param value: Value to set in self._program_state.
        """
        self._program_state[key] = value

    @classmethod
    def from_context(cls):
        """Retrieve this class' instance from the current Click context.

        :return: Instance of this class.
        :rtype: Config
        """
        try:
            ctx = CLICK_COMMAND.get_current_context()
            print("*************************")
            print(ctx)
            print("*************************")
        except RuntimeError:
            return cls()
        return ctx.find_object(cls)

    def pop(self, *args):
        """Pop item from self._program_state.

        :param iter args: Passed to self._program_state.

        :return: Object from self._program_state.pop().
        """
        return self._program_state.pop(*args)

    def update(self, params, ignore_set=False, overwrite=False):
        """Set instance values from dictionary.

        :param dict params: Click context params.
        :param bool ignore_set: Skip already-set values instead of raising AttributeError.
        :param bool overwrite: Allow overwriting already-set values.
        """
        log = logging.getLogger(__name__)
        valid = {i[0] for i in self}
        for key, value in params.items():
            if not hasattr(self, key):
                raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, key))
            if key not in valid:
                message = "'{}' object does not support item assignment on '{}'"
                raise AttributeError(message.format(self.__class__.__name__, key))
            if key in self._already_set:
                if ignore_set:
                    log.debug("%s already set in config, skipping.", key)
                    continue
                if not overwrite:
                    message = "'{}' object does not support item re-assignment on '{}'"
                    raise AttributeError(message.format(self.__class__.__name__, key))
            setattr(self, key, value)
            self._already_set.add(key)


class EventHandlers(object):
    """Hold Sphinx event handlers as static or class methods.

    :ivar multiprocessing.queues.Queue ABORT_AFTER_READ: Communication channel to parent process.
    :ivar bool BANNER_GREATEST_TAG: Banner URLs point to greatest/highest (semver) tag.
    :ivar str BANNER_MAIN_VERSION: Banner URLs point to this remote name (from Versions.__getitem__()).
    :ivar bool BANNER_RECENT_TAG: Banner URLs point to most recently committed tag.
    :ivar str CURRENT_VERSION: Current version being built.
    :ivar bool IS_ROOT: Value for context['scv_is_root'].
    :ivar bool SHOW_BANNER: Display the banner.
    :ivar sphinxcontrib.versioning.versions.Versions VERSIONS: Versions class instance.
    """

    ABORT_AFTER_READ = None
    BANNER_GREATEST_TAG = False
    BANNER_MAIN_VERSION = None
    BANNER_RECENT_TAG = False
    CURRENT_VERSION = None
    IS_ROOT = False
    SHOW_BANNER = False
    VERSIONS = None
    ASSETS_TO_COPY = []

    @staticmethod
    def builder_inited(app):
        """Update the Sphinx builder.

        :param sphinx.application.Sphinx app: Sphinx application object.
        """
        # Add this extension's _templates directory to Sphinx.
        templates_dir = os.path.join(os.path.dirname(__file__), "_templates")
        if app.builder.name != "latex":
            app.builder.templates.pathchain.insert(0, templates_dir)
            app.builder.templates.loaders.insert(0, SphinxFileSystemLoader(templates_dir))
            app.builder.templates.templatepathlen += 1

        # Add versions.html to sidebar.
        if "**" not in app.config.html_sidebars:
            # default_sidebars was deprecated in Sphinx 1.6+, so only use it if possible (to maintain
            # backwards compatibility), else don't use it.
            try:
                app.config.html_sidebars["**"] = StandaloneHTMLBuilder.default_sidebars + ["versions.html"]
            except AttributeError:
                app.config.html_sidebars["**"] = ["versions.html"]
        elif "versions.html" not in app.config.html_sidebars["**"]:
            app.config.html_sidebars["**"].append("versions.html")

        log.error(f"Theme: {app.config.html_theme}")
        # Insert flyout script
        if app.config.html_theme == "sphinx_rtd_theme":
            app.add_js_file("_rtd_versions.js")
            EventHandlers.ASSETS_TO_COPY.append("_rtd_versions.js")

    @classmethod
    def copy_custom_files(cls, app, exc):
        if app.builder.format == "html" and not exc:
            staticdir = os.path.join(app.builder.outdir, "_static")
            for asset in cls.ASSETS_TO_COPY:
                print(asset)
                copy_asset_file(f"{STATIC_DIR}/{asset}", staticdir)
                log.success(f"copying {STATIC_DIR}/{asset} to {staticdir}")

    @classmethod
    def env_updated(cls, app, env):
        """Abort Sphinx after initializing config and discovering all pages to build.

        :param sphinx.application.Sphinx app: Sphinx application object.
        :param sphinx.environment.BuildEnvironment env: Sphinx build environment.
        """
        if cls.ABORT_AFTER_READ:
            config = {n: getattr(app.config, n) for n in (a for a in dir(app.config) if a.startswith("scv_"))}
            config["found_docs"] = tuple(str(d) for d in env.found_docs)
            config["master_doc"] = str(app.config.master_doc)
            cls.ABORT_AFTER_READ.put(config)
            sys.exit(0)

    @classmethod
    def html_page_context(cls, app, pagename, templatename, context, doctree):
        """Update the Jinja2 HTML context, exposes the Versions class instance to it.

        :param sphinx.application.Sphinx app: Sphinx application object.
        :param str pagename: Name of the page being rendered (without .html or any file extension).
        :param str templatename: Page name with .html.
        :param dict context: Jinja2 HTML context.
        :param docutils.nodes.document doctree: Tree of docutils nodes.
        """
        assert templatename or doctree  # Unused, for linting.
        this_remote = "main"
        banner_main_remote = "main"
        # Update Jinja2 context.
        context["bitbucket_version"] = cls.CURRENT_VERSION
        context["current_version"] = cls.CURRENT_VERSION
        context["github_version"] = cls.CURRENT_VERSION
        context["html_theme"] = app.config.html_theme
        context["scv_banner_greatest_tag"] = cls.BANNER_GREATEST_TAG
        context["scv_banner_main_ref_is_branch"] = (
            banner_main_remote["kind"] == "heads" if cls.SHOW_BANNER else None
        )
        context["scv_banner_main_ref_is_tag"] = (
            banner_main_remote["kind"] == "tags" if cls.SHOW_BANNER else None
        )
        context["scv_banner_main_version"] = banner_main_remote["name"] if cls.SHOW_BANNER else None
        context["scv_banner_recent_tag"] = cls.BANNER_RECENT_TAG
        # context["scv_is_branch"] = this_remote["kind"] == "heads"
        # context["scv_is_greatest_tag"] = this_remote == versions.greatest_tag_remote
        # context["scv_is_recent_branch"] = this_remote == versions.recent_branch_remote
        # context["scv_is_recent_ref"] = this_remote == versions.recent_remote
        # context["scv_is_recent_tag"] = this_remote == versions.recent_tag_remote
        context["scv_is_root"] = cls.IS_ROOT
        # context["scv_is_tag"] = this_remote["kind"] == "tags"
        context["scv_show_banner"] = cls.SHOW_BANNER
        context["versions"] = cls.VERSIONS
        # context["vhasdoc"] = versions.vhasdoc
        # context["vpathto"] = versions.vpathto

        # Insert banner into body.
        if cls.SHOW_BANNER and "body" in context:
            parsed = app.builder.templates.render("banner.html", context)
            context["body"] = parsed + context["body"]
            # Handle overridden css_files.
            css_files = context.setdefault("css_files", list())
            if "_static/banner.css" not in css_files:
                css_files.append("_static/banner.css")
            # Handle overridden html_static_path.
            if STATIC_DIR not in app.config.html_static_path:
                app.config.html_static_path.append(STATIC_DIR)

        # Reset last_updated with file's mtime (will be last git commit authored date).
        if app.config.html_last_updated_fmt is not None:
            file_path = app.env.doc2path(pagename)
            if os.path.isfile(file_path):
                lufmt = app.config.html_last_updated_fmt or getattr(locale, "_")("%b %d, %Y")
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                context["last_updated"] = format_date(lufmt, mtime, language=app.config.language)


class ConfigInject(SphinxConfig):
    """Inject this extension info self.extensions. Append after user's extensions."""

    def __init__(self, *args):
        """Constructor."""
        super(ConfigInject, self).__init__(*args)
        self.extensions.append("sphinxcontrib.versioning.sphinx_")


def setup(app):
    """Called by Sphinx during phase 0 (initialization).

    :param sphinx.application.Sphinx app: Sphinx application object.

    :returns: Extension version.
    :rtype: dict
    """
    # Used internally. For rebuilding all pages when one or versions fail.
    app.add_config_value("sphinxcontrib_versioning_versions", SC_VERSIONING_VERSIONS, "html")

    # Needed for banner.
    if not app.config.html_static_path:
        app.config.html_static_path.append(STATIC_DIR)

    # Tell Sphinx which config values can be set by the user.
    for name, default in Config():
        app.add_config_value("scv_{}".format(name), default, "html")

    # Event handlers.
    app.connect("builder-inited", EventHandlers.builder_inited)
    app.connect("env-updated", EventHandlers.env_updated)
    app.connect("html-page-context", EventHandlers.html_page_context)
    app.connect("build-finished", EventHandlers.copy_custom_files)
    return dict(version=__version__)
