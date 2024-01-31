"""Interface with Sphinx."""

import os
import sys

from loguru import logger as log
from sphinx.jinja2glue import SphinxFileSystemLoader
from sphinx.builders.html import StandaloneHTMLBuilder

from sphinx_versioned._version import __version__
from sphinx.util.fileutil import copy_asset_file

SC_VERSIONING_VERSIONS = list()  # Updated after forking.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "_static")


class EventHandlers(object):
    """Holds Sphinx event handlers as static or class methods.

    Parameters
    ----------
    ABORT_AFTER_READ : `bool` or `~multiprocessing.queues.Queue`
        Communication channel to parent process
    CURRENT_VERSION : `str`
        Current version being built.
    VERSIONS : `~sphinx_versioned.versions.BuiltVersions`
        Pass through versions for them to be linked to be linked in the badge.
    ASSETS_TO_COPY : `list`
        Assest to copy to output directory.
    RESET_INTERSPHINX_MAPPING : `bool`
        Reset intersphinx mapping after each build.
    """

    ABORT_AFTER_READ = None
    CURRENT_VERSION = None
    VERSIONS = None
    ASSETS_TO_COPY = []
    RESET_INTERSPHINX_MAPPING = False

    @staticmethod
    def builder_inited(app):
        """Update the Sphinx builder.

        Parameters
        ----------
        app : `~param sphinx.application.Sphinx`
            Sphinx application object.
        """
        # Add this extension's _templates directory to Sphinx.
        templates_dir = os.path.join(os.path.dirname(__file__), "_templates")
        log.debug(f"Templates dir: {templates_dir}")
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
        if app.config.html_theme == "bootstrap-astropy":
            app.add_js_file("_rtd_versions.js")
            EventHandlers.ASSETS_TO_COPY.append("_rtd_versions.js")
            app.add_css_file("badge_only.css")
            EventHandlers.ASSETS_TO_COPY.append("badge_only.css")
            EventHandlers.ASSETS_TO_COPY.append("fontawesome-webfont.woff")

    @classmethod
    def builder_finished_tasks(cls, app, exc):
        if cls.RESET_INTERSPHINX_MAPPING:
            log.debug("Reset intersphinx mappings")
            for key, value in app.config.intersphinx_mapping.values():
                app.config.intersphinx_mapping[key] = value
            log.debug(app.config.intersphinx_mapping)

        if app.builder.format == "html" and not exc:
            staticdir = os.path.join(app.builder.outdir, "_static")
            for asset in cls.ASSETS_TO_COPY:
                copy_asset_file(f"{STATIC_DIR}/{asset}", staticdir)
                log.debug(f"copying {STATIC_DIR}/{asset} to {staticdir}")

    @classmethod
    def env_updated(cls, app, env):
        """Abort Sphinx after initializing config and discovering all pages to build.

        Parameters
        ----------
        app : `~sphinx.application.Sphinx`
            Sphinx application object.
        env : `~sphinx.environment.BuildEnvironment`
            Sphinx build environment
        """
        if cls.ABORT_AFTER_READ:
            config = {n: getattr(app.config, n) for n in (a for a in dir(app.config) if a.startswith("sv_"))}
            config["found_docs"] = tuple(str(d) for d in env.found_docs)
            config["master_doc"] = str(app.config.master_doc)
            cls.ABORT_AFTER_READ.put(config)
            sys.exit(0)

    @classmethod
    def html_page_context(cls, app, pagename, templatename, context, doctree):
        """Update the Jinja2 HTML context, exposes the Versions class instance to it.

        Parameters
        ----------
        app : `~sphinx.application.Sphinx`
            Sphinx application object.
        pagename : `str`
            Name of the page being rendered (without .html or any file extension).
        templatename : `str`
            Page name with .html.
        context : `dict`
            Jinja2 HTML context.
        doctree : `~docutils.nodes.document`
            Tree of docutils nodes.
        """
        assert templatename or doctree  # Unused, for linting.
        this_remote = "main"

        # Update Jinja2 context.
        context["github_version"] = cls.CURRENT_VERSION
        context["current_version"] = cls.CURRENT_VERSION
        context["html_theme"] = app.config.html_theme
        context["versions"] = cls.VERSIONS

        # Relative path to master_doc
        relpath = (pagename.count("/")) * "../"
        context["relpath"] = relpath
        return


def setup(app):
    """Called by Sphinx during phase 0 (initialization).

    Parameters
    ----------
    app : `~sphinx.application.Sphinx`
        Sphinx application object.

    Returns
    -------
    extension version : `dict`
    """
    # Used internally. For rebuilding all pages when one or versions fail.
    # app.add_config_value("sphinx_versioned_versions", SC_VERSIONING_VERSIONS, "html")

    # Needed for banner.
    if not app.config.html_static_path:
        app.config.html_static_path.append(STATIC_DIR)

    # Tell Sphinx which config values can be set by the user.
    # for name, default in Config():
    #     app.add_config_value("sv_{}".format(name), default, "html")

    # Event handlers.
    app.connect("builder-inited", EventHandlers.builder_inited)
    app.connect("env-updated", EventHandlers.env_updated)
    app.connect("html-page-context", EventHandlers.html_page_context)
    app.connect("build-finished", EventHandlers.builder_finished_tasks)
    return dict(version=__version__)
