"""Interface with Sphinx."""

import os

from loguru import logger as log
from sphinx.util.fileutil import copy_asset_file
from sphinx.jinja2glue import SphinxFileSystemLoader
from sphinx.builders.html import StandaloneHTMLBuilder

from sphinx_versioned._version import __version__

STATIC_DIR = os.path.join(os.path.dirname(__file__), "_static")


class EventHandlers(object):
    """Holds Sphinx event handlers as static or class methods.

    Parameters
    ----------
    CURRENT_VERSION : :class:`str`
        Current version being built.
    VERSIONS : :class:`sphinx_versioned.versions.BuiltVersions`
        Pass through versions for them to be linked to be linked in the badge.
    ASSETS_TO_COPY : :class:`list`
        Assest to copy to output directory.
    RESET_INTERSPHINX_MAPPING : :class:`bool`
        Reset intersphinx mapping after each build.
    """

    CURRENT_VERSION: str = None
    VERSIONS = None
    ASSETS_TO_COPY: set = set()
    RESET_INTERSPHINX_MAPPING: bool = False

    @classmethod
    def builder_inited(cls, app) -> None:
        """Update the Sphinx builder.

        Parameters
        ----------
        app : :class:`sphinx.application.Sphinx`
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

        # Add css properties to bold currently-active branch/tag
        app.add_css_file("_rst_properties.css")
        cls.ASSETS_TO_COPY.add("_rst_properties.css")

        # Insert flyout script
        if app.config.html_theme == "bootstrap-astropy":
            app.add_js_file("_rtd_versions.js")
            app.add_css_file("badge_only.css")
            cls.ASSETS_TO_COPY.add("_rtd_versions.js")
            cls.ASSETS_TO_COPY.add("badge_only.css")
            cls.ASSETS_TO_COPY.add("fontawesome-webfont.woff")
        return

    @classmethod
    def builder_finished_tasks(cls, app, exc) -> None:
        """Method to execute tasks after the sphinx builder is finished.

        Parameters
        ----------
        app : :class:`sphinx.application.Sphinx`
            Sphinx application object.
        exc : :class:`Exception`
            Exception.
        """
        if cls.RESET_INTERSPHINX_MAPPING:
            log.debug("Reset intersphinx mappings")
            for key, value in app.config.intersphinx_mapping.values():
                app.config.intersphinx_mapping[key] = value
            log.debug(app.config.intersphinx_mapping)

        if app.builder.format == "html" and not exc:
            staticdir = os.path.join(app.builder.outdir, "_static")

            for asset in cls.ASSETS_TO_COPY:
                copy_asset_file(f"{STATIC_DIR}/{asset}", staticdir)
                log.debug(f"copying `{asset}`: {STATIC_DIR}/{asset} to {staticdir}")

            # Reset Assets to copy
            cls.ASSETS_TO_COPY.clear()
        return

    @classmethod
    def html_page_context(cls, app, pagename, templatename, context, doctree) -> None:
        """Update the Jinja2 HTML context, exposes the Versions class instance to it.

        Parameters
        ----------
        app : :class:`sphinx.application.Sphinx`
            Sphinx application object.
        pagename : :class:`str`
            Name of the page being rendered (without .html or any file extension).
        templatename : :class:`str`
            Page name with .html.
        context : :class:`dict`
            Jinja2 HTML context.
        doctree : :class:`docutils.nodes.document`
            Tree of docutils nodes.
        """
        assert templatename or doctree  # Unused, for linting.
        this_remote = "main"

        # Update Jinja2 context.
        context["github_version"] = cls.CURRENT_VERSION
        context["current_version"] = cls.CURRENT_VERSION
        context["html_theme"] = app.config.html_theme
        context["project_url"] = app.config.sv_project_url
        context["versions"] = cls.VERSIONS

        # Relative path to master_doc
        relpath = (pagename.count("/")) * "../"
        context["relpath"] = relpath
        return


def setup(app) -> dict:
    """Called by Sphinx during phase 0 (initialization).

    Parameters
    ----------
    app : :class:`sphinx.application.Sphinx`
        Sphinx application object.

    Returns
    -------
    extension version : :class:`dict`
    """
    # Used internally. For rebuilding all pages when one or versions fail.
    # app.add_config_value("sphinx_versioned_versions", SC_VERSIONING_VERSIONS, "html")

    # Needed for banner.
    if not app.config.html_static_path:
        app.config.html_static_path.append(STATIC_DIR)

    # Tell Sphinx which config values can be set by the user.
    app.add_config_value("sv_project_url", None, "html")

    # Event handlers.
    app.connect("builder-inited", EventHandlers.builder_inited)
    app.connect("html-page-context", EventHandlers.html_page_context)
    app.connect("build-finished", EventHandlers.builder_finished_tasks)
    return dict(version=__version__)
