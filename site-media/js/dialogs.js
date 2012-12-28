var dlg = null;
var escape_handler = null;
var return_handler = null;

document.onkeydown = function(evt)
{
    var Esc = window.event? 27 : evt.DOM_VK_ESCAPE; // MSIE : Firefox
    var Return = window.event? 13 : evt.DOM_VK_RETURN; // MSIE : Firefox
    if (escape_handler && evt.keyCode == Esc)
        escape_handler();
    else if (return_handler && evt.keyCode == Return)
        return_handler();
}

var Dialog = {};
Dialog.Box = Class.create();
Object.extend(Dialog.Box.prototype, {
  initialize: function(id) {
    this.createOverlay();

    this.dialog_box = $(id);
    this.dialog_box.show = this.show.bind(this);
    this.dialog_box.hide = this.hide.bind(this);

    this.parent_element = this.dialog_box.parentNode;

    var e_dims = Element.getDimensions(this.dialog_box);
    var b_dims = Element.getDimensions(this.overlay);
    this.dialog_box.style.position = "absolute";
    this.dialog_box.style.left = '0';//((b_dims.width/2) - (e_dims.width/2)) + 'px';
    this.dialog_box.style.top = '0';
    this.dialog_box.style.zIndex = this.overlay.style.zIndex + 1;
  },

  createOverlay: function() {
    if($('dialog_overlay')) {
      this.overlay = $('dialog_overlay');
    } else {
      this.overlay = document.createElement('div');
      this.overlay.id = 'dialog_overlay';
      Object.extend(this.overlay.style, {
        position: 'absolute',
        top: 0,
        left: 0,
        zIndex: 90,
        width: '100%',
        backgroundColor: '#000',
        display: 'none'
      });
      document.body.insertBefore(this.overlay, document.body.childNodes[0]);
    }
  },

  moveDialogBox: function(where) {
    Element.remove(this.dialog_box);
    if(where == 'back')
      this.dialog_box = this.parent_element.appendChild(this.dialog_box);
    else
      this.dialog_box = this.overlay.parentNode.insertBefore(this.dialog_box, this.overlay);
  },

  show: function() {
    this.overlay.style.height = getPageSize()[1]+'px';//"100%";//$('body').getHeight()+'px';
    this.moveDialogBox('front');
    this.overlay.onclick = this.hide.bind(this);
    this.selectBoxes('hide');
    new Effect.Appear(this.overlay, {duration: 0.1, from: 0.0, to: 0.3});
    var arrayPageScroll = getPageScroll();
    var lightboxTop = arrayPageScroll[1] - 50 + (arrayPageSize[3] / 10);
    var lightboxLeft = arrayPageScroll[0];
    this.dialog_box.style.top = lightboxTop+'px';
    this.dialog_box.style.left = lightboxLeft+'px';
    this.dialog_box.style.display = '';
    hideFlash();
  },

  hide: function() {
    this.selectBoxes('show');
    new Effect.Fade(this.overlay, {duration: 0.1});
    this.dialog_box.style.display = 'none';
    this.moveDialogBox('back');
    $A(this.dialog_box.getElementsByTagName('input')).each(function(e){if(e.type!='submit')e.value=''});
    showFlash();
  },

  selectBoxes: function(what) {
    $A(document.getElementsByTagName('select')).each(function(select) {
      Element[what](select);
    });

    if(what == 'hide')
      $A(this.dialog_box.getElementsByTagName('select')).each(function(select){Element.show(select)})
  }
});

function init_dialog()
{
    if (dlg != null)
        return;

    var div = document.createElement("div");
    div.id = "id_popup_dialog";
    document.body.appendChild(div);
    
    var form = document.createElement("div");
    form.id = "id_popup_dialog_content";
    div.appendChild(form);
    
    var tmp = document.createElement("h2");
    tmp.id = "dialog_header";
    form.appendChild(tmp)
    
    tmp = document.createElement("div");
    tmp.id = 'dialog_explanation';
    form.appendChild(tmp)
    
    tmp = document.createElement("div");
    tmp.style.textAlign = 'right';
    tmp.id = 'dialog_buttons';
    form.appendChild(tmp)

    dlg = new Dialog.Box('id_popup_dialog');
}

function show_dialog(params)
{
    init_dialog();
    $("dialog_header").innerHTML = params.header;
    $("dialog_explanation").innerHTML = params.explanation;
    
    remove_children_from_node($("dialog_buttons"));
    params.buttons.each(function(button){add_dialog_button(button);})
    
    $('id_popup_dialog').show();
}

function add_dialog_button(button)
{
    var new_button = document.createElement('input');
    new_button.type = "button";
    new_button.value = button.name;
    if (button.hotkey == "return")
        return_handler = function(){ new_button.click(); return_handler = null; };
    else if (button.hotkey == "escape")
        escape_handler = function(){ new_button.click(); escape_handlers = null; };
    else
        new_button.accesskey = button.hotkey;

    new_button.onclick = 'action' in button? function(){ button.action(); dlg.hide(); }: function(){ dlg.hide(); };

    $("dialog_buttons").appendChild(new_button);
    $("dialog_buttons").appendChild(document.createTextNode(" "));
}