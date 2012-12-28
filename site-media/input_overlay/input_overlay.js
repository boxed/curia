$j = jQuery;

function overlay_blur_function() {
    var default_value = $j(this).attr('default_value');
    if ($j.trim(this.value) == '') {
    	this.value = (default_value ? default_value : '');
    	$j(this).removeClass("focusField").addClass("defaultIdleField");
	}
	else {
	    $j(this).removeClass("focusField").addClass("idleField");
	}
}

function overlay_focus_function() {
    var default_value = $j(this).attr('default_value');
	$j(this).removeClass("idleField").removeClass("defaultIdleField").addClass("focusField");
    if (this.value == default_value) { 
    	this.value = '';
	}
	if(this.value != default_value) {
		this.select();
	}
}

function updateInputOverlays() {
	function setupDefaultHandling(i) {
		var default_value = $j(this).attr('default_value');
		if (default_value) {
		    if ($j(this).val() == '') {
    		    $j(this).val(default_value);
    		    $j(this).addClass("defaultIdleField");
		    }
       		$j(this).focus(overlay_focus_function);
    		$j(this).blur(overlay_blur_function);
		}
	}
	$j('input[type="text"]').each(setupDefaultHandling);
	$j('input[type="password"]').each(setupDefaultHandling);
}
$j(document).ready(function() {
	updateInputOverlays();
});			
