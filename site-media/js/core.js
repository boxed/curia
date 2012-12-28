function do_nothing(){}

function has_class(obj, cl)
{
    var s = obj.className.split(" ");
    var r = "";
    for (var i = 0; i != s.length; i++)
    {
        if (s[i] == cl)
            return true;
    }

    return false;
}

function remove_children_from_node(node)
{
    while (node.childNodes.length != 0)
    node.removeChild(node.childNodes[0]);
}

function create_element(type, params)
{
    var element = document.createElement(type);
    for (var i in params)
    {
        if (i == "style")
        {
            for (var j in params[i])
                element.style[j] = element.style[j];
        }
        else
            element[i] = params[i];
    }
        
    return element;
}

function call_function_with_data_from(func, url)
{
    call_function_with_data_from(func, url, '')
}

function call_function_with_data_from(func, url, params)
{
    if (!params)
        params = {};
    new Ajax.Request(url, 
        {
            method:'post',
            parameters:params,
            onSuccess: function(request)
            {
                var p = eval('('+request.responseText+')');
                func(p);
            },
            onFailure: function(request)
            {
                //alert('fail: '+request.responseText);
            }
        });
}

function call_function_with_raw_data_from(func, url)
{
    return call_function_with_raw_data_from(func, url, 'post', {});
}

function call_function_with_raw_data_from(func, url, method, params)
{
    params.hack = String(Math.random());
    new Ajax.Request(url, 
        {
            method:method,
            parameters:params,
            onComplete: function(request)
            {
                func(request.responseText);
            }
        });
}

function remove_element(id)
{
    var element = document.getElementById(id);
    if (element)
        element.parentNode.removeChild(element);
}

function remove_elements(list)
{
    for (var i in list)
        remove_element(list[i]);
}

function quickElement() {
    var obj = document.createElement(arguments[0]);
    if (arguments[2] != '' && arguments[2] != null) {
        var textNode = document.createTextNode(arguments[2]);
        obj.appendChild(textNode);
    }
    var len = arguments.length;
    for (var i = 3; i < len; i += 2) {
        obj.setAttribute(arguments[i], arguments[i+1]);
    }
    arguments[1].appendChild(obj);
    return obj;
}

function log(s)
{
    quickElement('div', document.getElementById('test'), s);
}

function pad(number, length)
{
    var s = ''+number;
    while (s.length < length)
        s = '0' + s;
    return s;
}

function parse_date(s)
{
    var date = new Object();
    date.year = parse_int(s.substr(0, 4));
    date.month = parse_int(s.substr(5, 2));
    date.date = parse_int(s.substr(8, 2));
    return date;
}

function parse_datetime(s)
{
    var date = new Object();
    date.year = parse_int(s.substr(0, 4));
    date.month = parse_int(s.substr(5, 2));
    date.date = parse_int(s.substr(8, 2));
    date.hour = parse_int(s.substr(11, 2));
    date.minute = parse_int(s.substr(14, 2));
    date.second = parse_int(s.substr(17, 2));
    return date;
}

function parse_int(s)
{
    // always parse in base 10, don't rely on the stupid autodetection that will turn "010" into the number 8
    return parseInt(s,10);
}

function replace_contents_with_data_from(id, url, extra_tags_to_delete)
{
    if (typeof(extra_tags_to_delete) != 'undefined')
    {
        for (i in extra_tags_to_delete)
        {
            var extra_element = document.getElementById(extra_tags_to_delete[i]);
            if (extra_element != null)
                extra_element.parentNode.removeChild(extra_element);
        }
    }
    
    var element = document.getElementById(id);
    element.innerHTML = gettext("Loading...");

    var form = create_form_to_url(url);
    
    // bind to form
    var bindArgs =
    {
        formNode: form,
        mimetype: "text/html",
        transport: "IframeTransport",
        handle: function(type, data, evt)
        {
            if (data.body.innerHTML == "")
                element.parentNode.removeChild(element);
            else 
                element.innerHTML = data.body.innerHTML;

            if (form_container)
                form_container.removeChild(form);
        }
    };
    var request = dojo.io.bind(bindArgs);
}

function add_load_event(func) 
{
    var oldonload = window.onload;
    if (typeof window.onload != 'function') 
        window.onload = func;
    else 
    {
        window.onload = function() 
        {
            oldonload();
            func();
        }
    }
}

function prepare_x_for_help_messages(x)
{
    var inputs = document.getElementsByTagName(x);
    for (var i=0; i<inputs.length; i++)
    {
        // test to see if the help span exists first
        if ($(inputs[i].parentNode).getElementsByClassName("help_text")[0]) 
        {
            // the span exists!  on focus, show the help
            inputs[i].onfocus = function()
            {
                $(this.parentNode).getElementsByClassName("help_text")[0].style.display = "inline";
            }
            // when the cursor moves away from the field, hide the help
            inputs[i].onblur = function()
            {
               $(this.parentNode).getElementsByClassName("help_text")[0].style.display = "none";
            }
        }
    }
}

function prepare_inputs_for_help_messages() 
{
    prepare_x_for_help_messages("input");
    prepare_x_for_help_messages("select");
    prepare_x_for_help_messages("textarea");
}

function goto_url(event)
{
    e = Event.element(event);
    /*if (external resource, we can't just check the beginning of the URL) 
    {
        // TODO: open new window with the url
    }
    else 
    {*/
    new Ajax.Request(e.href, 
        {
            method:'get',
            parameters: {'json-request':true}
        })
    Event.stop(event);
}

function scroll_to_and_flash(id)
{
    new Effect.ScrollTo(id, {duration:0.5});
    new Effect.Pulsate(id);
}

function fix_button_behavior() {
    $$(".button").each(function(button) {
        button.onmouseover = function() { this.className += " hover"; }
        button.onmouseout = function() { this.className = this.className.replace(" hover", "").replace(" active", ""); }
        button.onmousedown = function() { this.className += " active"; }
        button.onmouseup = function() { this.className = this.className.replace(" active", ""); }
    });
}
Event.observe(window, "load", fix_button_behavior);