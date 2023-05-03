"""Interface with Sphinx."""

import os
import sys

from loguru import logger as log
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.jinja2glue import SphinxFileSystemLoader

from sphinx_versioned._version import __version__
from sphinx.util.fileutil import copy_asset_file

SC_VERSIONING_VERSIONS = list()  # Updated after forking.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "_static")


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
        log.info(f"Templates dir: {templates_dir}")
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

        log.info(f"Theme: {app.config.html_theme}")
        # Insert flyout script
        if app.config.html_theme == "sphinx_rtd_theme" or app.config.html_theme == "bootstrap-astropy":
            app.add_js_file("_rtd_versions.js")
            EventHandlers.ASSETS_TO_COPY.append("_rtd_versions.js")
        if app.config.html_theme == "bootstrap-astropy":
            app.add_css_file("badge_only.css")
            EventHandlers.ASSETS_TO_COPY.append("badge_only.css")
            EventHandlers.ASSETS_TO_COPY.append("fontawesome-webfont.woff")

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
        context["scv_is_root"] = cls.IS_ROOT
        context["versions"] = cls.VERSIONS


def setup(app):
    """Called by Sphinx during phase 0 (initialization).

    :param sphinx.application.Sphinx app: Sphinx application object.

    :returns: Extension version.
    :rtype: dict
    """
    # Used internally. For rebuilding all pages when one or versions fail.
    # app.add_config_value("sphinx_versioned_versions", SC_VERSIONING_VERSIONS, "html")

    # Needed for banner.
    if not app.config.html_static_path:
        app.config.html_static_path.append(STATIC_DIR)

    # Tell Sphinx which config values can be set by the user.
    # for name, default in Config():
    #     app.add_config_value("scv_{}".format(name), default, "html")

    # Event handlers.
    app.connect("builder-inited", EventHandlers.builder_inited)
    app.connect("env-updated", EventHandlers.env_updated)
    app.connect("html-page-context", EventHandlers.html_page_context)
    app.connect("build-finished", EventHandlers.copy_custom_files)
    return dict(version=__version__)
