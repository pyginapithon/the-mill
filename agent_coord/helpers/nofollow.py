# -*- coding: utf-8 -*-
"""One HTTP opener that never follows a redirect (#654).

A 3xx comes back as urllib.error.HTTPError, so a credential sent to the first
URL is never carried to a second one. The wall's wake POST and the client's
verb calls and CA fetch share it.
"""
from __future__ import annotations

import ssl
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse every redirect: the caller checked the first URL only."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def open_no_redirect(req, *, timeout: float, context: ssl.SSLContext | None = None):
    """Open req once. A 3xx raises HTTPError; nothing is sent to its Location."""
    handlers: list = [NoRedirect]
    if context is not None:
        handlers.append(urllib.request.HTTPSHandler(context=context))
    return urllib.request.build_opener(*handlers).open(req, timeout=timeout)
