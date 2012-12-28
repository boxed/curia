Event.observe(window, 'load', init_inline_edit, false);

function init_inline_edit() {
    $$('.inline_editable').each(
        function(div)
        {
            makeEditable(div);
        }
    );
}

function makeEditable(id) {
    Event.observe(id, 'click', function(){edit($(id))}, false);
    Event.observe(id, 'mouseover', function(){showAsEditable($(id))}, false);
    Event.observe(id, 'mouseout', function(){showAsEditable($(id), true)}, false);
}


function showAsEditable(obj, clear) {
    if (!clear) {
        Element.addClassName(obj, 'editable');
    } else {
        Element.removeClassName(obj, 'editable');
    }
}

function edit(obj) {
    Element.hide(obj);
    var textbox ='<form class="form" id="' + obj.id + '_editor" onSubmit="return false;"><input style="width:100%" type="text" name="' + obj.id + '" id="' + obj.id + '_edit" value="'+obj.innerHTML+'" />';
    new Insertion.After(obj, textbox);

    Event.observe(obj.id+'_edit', 'blur', function(){cleanUp(obj)}, false);
    Event.observe(obj.id+'_editor', 'submit', function(e){saveChanges(obj, obj.getAttribute('edit_url'));}, false);
    $(obj.id+'_edit').focus();
}

function cleanUp(obj, keepEditable) {
    Element.remove(obj.id+'_editor');
    Element.show(obj);
    if (!keepEditable) showAsEditable(obj, true);
}

function saveChanges(obj, url) {
    var new_content = $F(obj.id+'_edit');

    obj.innerHTML = "Saving...";
    cleanUp(obj);

    var success = function(t){editComplete(t, obj);}
    var failure = function(t){editFailed(t, obj);}

    var params = 'new_content=' + new_content.replace('&', '%26');
    var myAjax = new Ajax.Request(url, {method:'post', postBody:params, onSuccess:success, onFailure:failure});
}


function editComplete(t, obj) {
    obj.innerHTML = t.responseText;
    showAsEditable(obj, true);
}

function editFailed(t, obj) {
    obj.innerHTML = 'Sorry, the update failed.'+t.responseText;
    cleanUp(obj);
}
