# -*- coding: utf-8 -*-
# Copyright: (C) 2020 Lovac42
# Support: https://github.com/lovac42/DancingBaloney
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


import sys
import aqt
from aqt import mw
from anki.hooks import wrap, addHook

from .lib.com.lovac42.anki.version import CCBC, ANKI21

from .const import *
from .utils import *
from .style import *

from .config import Config
conf = Config(ADDON_NAME)

from .gui import Manager
mang = Manager(conf)


beforeResetState = "deckBrowser"


def bundledCSS(webview, fname, _old):
    ret = None
    theme = conf.get("theme")

    if not isinstance(webview, aqt.editor.EditorWebView):
        if mw.state == "resetRequired" and fname == "webview.css":
        # Filter out webview.css call by browser editor, editor, and clayout
            for i in range (1,12):
            #Filter out webview called from resetState in mw only
                try:
                    if "resetRequiredState" in sys._getframe(i).f_code.co_name:
                        fname = "resetRequired.css"
                except ValueError:
                    break
        elif fname == "reviewer.css":
        #Filter out reviewer.css called by clayout and preview
            for i in range (1,16):
                try:
                    if sys._getframe(i).f_code.co_name in (
                        "_onCardLayout", "_setupPreviewWebview",
                        "renderPreview", "_renderPreview"
                    ):
                        return _old(webview, fname)
                except ValueError:
                    break


    if theme:
        theme = f"theme/{theme}"
        css, custom_css = themeLoader(webview, fname, theme)
    else:
        css, custom_css = manualLoader(webview, fname)
        theme = "user_files"

    # Custom style sheets
    if custom_css:
        ret = getCustomPath(custom_css, theme)
    if ret == None:
        ret = _old(webview, fname)
    if css:
        if CCBC:
            return f"{ret}\n{css}"
        return f"{ret}\n<style>{css}</style>"
    return ret




def themeLoader(webview, fname, theme):
    css = ""

    if fname in (
        "deckbrowser.css","overview.css","reviewer.css",
        "toolbar-bottom.css","reviewer-bottom.css",
        "resetRequired.css"
    ):
        color = conf.get("theme_bg_color", "")
        bg = f"{mw.state}_{fname[:-4]}.jpg"

        # Note: Can't change opacity on different versions/platforms.
        # So theme_opacity is limited to the main view only.
        if "bottom" in fname:
            op = 100
            color = ""
        elif mw.state == "review" or \
        (mw.state == "resetRequired" and beforeResetState == 'review'):
            op = conf.get("theme_rev_opacity", 100)
        else:
            op = conf.get("theme_opacity", 100)
        css = getCSS(webview, color, bg, op, theme=theme)

        btn_bg = f"btn_{bg}"
        css += getButtonImage(webview, MOD_DIR, btn_bg, 80, theme)

        if ANKI21 and "deckbr" in fname:
            gear_bg = f"gear.png"
            css += getGearImage(webview, MOD_DIR, gear_bg, theme)

    return css, fname



def manualLoader(webview, fname):
    css = ""

    if mw.state == "review":
        # One or the other, targets different versions
        clearBackground(webview)
        clearBackground(mw.toolbar.web)

    elif fname == "toolbar.css" and mw.state == "deckBrowser":
        if not conf.get("top_toolbar_bg_img"):
            clearBackground(mw.toolbar.web)
        color = conf.get("top_toolbar_bg_color", "#F6FFE9")
        if color:
            css = setBGColor(webview, color, top=True)
        #Note: Images for toolbar is set in onAfterStateChange
        #      after page has been loaded.

    elif fname in ("deckbrowser.css","overview.css","resetRequired.css"):
        #TODO: sep settings for overview
        color = conf.get("bg_color", "#3B6EA5") #win2k default blue
        bg = conf.get("bg_img","sheep.gif")
        op = conf.get("bg_img_opacity", 100)
        r = conf.get("mw_img_rotate", 0)
        z = conf.get("mw_img_zoom", 100)
        css = getCSS(webview, color, bg, op, r, z)

        gear_bg = conf.get("gear_img")
        css += getGearImage(webview, MOD_DIR, gear_bg)

    elif fname == "toolbar-bottom.css":
        color = conf.get("bottom_toolbar_bg_color", "#3B6EA5")
        bg = conf.get("bottom_toolbar_bg_img")
        op = conf.get("bottom_toolbar_bg_img_opacity", 100)
        css = getCSS(webview, color, bg, op)

    custom_css = conf.get(f"custom_{fname[:-4]}_style")
    return css, custom_css


def onAfterStateChange(newS, oldS, *args):
    "This is needed to get around an issue with setting images on the toolbar."

    global beforeResetState
    beforeResetState = newS

    bg = None
    theme = conf.get("theme")
    if theme:
        bg = f"{newS}_toolbar.jpg"
        theme = f"theme/{theme}"
    elif newS == "review":
        clearBackground(mw.toolbar.web)
    else:
        bg = conf.get("top_toolbar_bg_img")
        theme = "user_files"

    #TODO: make theme specific
    #Sets menubar colors
    color = conf.get("menubar_txt_color")
    bgColor = conf.get("menubar_bg_color")
    setMenubarColor(color, bgColor)

    if bg:
        setImageWithJS(mw.toolbar.web, MOD_DIR, bg, theme)


# ===== EXEC ===========

def onProfileLoaded():
    aqt.webview.AnkiWebView.bundledCSS = wrap(
        aqt.webview.AnkiWebView.bundledCSS,
        bundledCSS,
        "around"
    )
    mw.reset(True)
    addHook(f"{ADDON_NAME}.configUpdated", lambda:mw.reset(True))

#reloads with config.json data
addHook("profileLoaded", onProfileLoaded)
addHook('afterStateChange', onAfterStateChange)
