from anki import hooks
from anki.template import TemplateRenderContext
from aqt import dialogs, gui_hooks, mw
from aqt.browser import PreviewDialog
from aqt.clayout import CardLayout
from aqt.qt import Qt
from aqt.qt import QApplication
from aqt.reviewer import Reviewer
from aqt.qt import (
    QAction,
    QApplication,
    QKeySequence,
    QMenu,
    QShortcut,
    qconnect,
)
from aqt.browser import Browser
from anki.hooks import addHook

# import aqt to access the function to add css files
import aqt
from typing import Any, Optional

# Responding to clicks
############################
from aqt.utils import tooltip

from anki.utils import json
from aqt.editor import Editor

import re


from aqt import mw
config = mw.addonManager.getConfig(__name__)

## TO DO ##
# Add a way to select card from the browser directly
# Find out how to modify this css directly within Anki
# Find a icon for the editor

# this part of the code is adapted from Clickable Tags v20 Anki 2120 support from the AnKing team

# this function opens the browser and launch a research
def on_js_message_clickable_cards(handled, msg, context):
    if isinstance(context, CardLayout) and (
        msg.startswith("cards_ct_click") or msg.startswith("cards_ct_dbclick")
    ):
        # card layout is a modal dialog, so we can't display there
        tooltip("Can't be used in card layout screen.")
        return handled

    if not isinstance(context, Reviewer) and not isinstance(context, PreviewDialog):
        # only function in review and preview screens
        return handled

    # the relevant message will start with ct_click for both simple and double click
    if msg.startswith("cards_ct_click"):
        nid = msg.replace("cards_ct_click", "")
        browser = dialogs.open("Browser", mw)
        browser.setFilter('"nid:%s"' % nid)
        return True, None

    return handled

gui_hooks.webview_did_receive_js_message.append(on_js_message_clickable_cards)

# this adds the js to the card 
add_to_card = """
<script type="text/javascript">
function cards_ct_click(nid) {
    pycmd("cards_ct_click" + nid)
}
</script>
"""

def on_card_render_clickable_cards(output, context):
    output.question_text += add_to_card
    output.answer_text += add_to_card

hooks.card_did_render.append(on_card_render_clickable_cards)

# this part of the code is adapted from editor wrap selected text with custom html (addon removed from ankiweb)

# add custom css for the button
# give access permission
mw.addonManager.setWebExports(__name__, r'.+\.css')
addon_package = mw.addonManager.addonFromModule(__name__)
# base_url for css files
base_url_css = f'/_addons/{addon_package}/user_files/clickable_cards.css'

# load css
def addCss_clickable_cards(web_content: aqt.webview.WebContent, context: Optional[Any]) -> None:
    # maybe should I restrict the loading to the corresponding window?
    web_content.css.append(base_url_css)

gui_hooks.webview_will_set_content.append(addCss_clickable_cards)

# adds the tags to selected text
def multi_wrap_clickable_cards(editor):
    text = editor.web.selectedText()
    text = re.findall("[0-9]+", text)[0]
    template = """<kbd class="clickable_cards" onclick="cards_ct_click('{nid}')" ondblclick="cards_ct_click('{nid}')">{nid}</kbd>&nbsp;"""
    output = template.format(nid=text)
    html = f"""setFormat('inserthtml', {json.dumps(output)});"""
    editor.web.eval(html)
                
# creates a button              
def setupEditorButtonsCardLinker(buttons, editor):
    buttons.append(editor.addButton(
        icon=None,
        cmd="multi_wrap_clickable_cards",
        func=lambda editor: multi_wrap_clickable_cards(editor),
        tip="Link card via (Ctrl+Alt+L)",
        label="Ln",
        keys="Ctrl+Alt+L"
        )
    )
    return buttons
    
addHook("setupEditorButtons", setupEditorButtonsCardLinker) 

# this part is adapted from link Cards Notes and Preview them in Extra window by ijgnd
# it adds a copy nid option to the right-click-opened menu in the browser

def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__.split(".")[0])
    if conf:
        return conf.get(arg, fail)
    else:
        return fail


pycmd_card = gc("prefix_cid")  # "card_in_extra_window"
pycmd_nid = gc("prefix_nid")  # "note_in_extra_window"

def nidcopy(nid):
    QApplication.clipboard().setText(str(nid))

def browser_shortcut_helper_nid(browser):
    if browser.card.nid:
        nidcopy(browser.card.nid)

def setup_menu_shortcut(self):
    browser = self
    try:
        m = self.menuLinking
    except:
        self.menuLinking = QMenu("&Linking")
        self.menuBar().insertMenu(self.mw.form.menuTools.menuAction(), self.menuLinking)
        m = self.menuLinking

    global action_copy_nid
    action_copy_nid = QAction(browser)
    action_copy_nid.setText("Copier nid")
    qconnect(action_copy_nid.triggered, lambda _, b=browser:browser_shortcut_helper_nid(b))
    ## this adds a shortcut to copy nid
    action_copy_nid.setShortcut("Ctrl+Alt+C")
    # ncombo = gc("shortcut: browser: copy nid")
    # if ncombo:
    #     action_copy_nid.setShortcut(QKeySequence(ncombo))
    m.addAction(action_copy_nid)

gui_hooks.browser_menus_did_init.append(setup_menu_shortcut)


def add_to_table_context_menu(browser, menu):
    menu.addAction(action_copy_nid)
gui_hooks.browser_will_show_context_menu.append(add_to_table_context_menu)