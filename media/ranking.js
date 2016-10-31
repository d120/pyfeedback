// Toggle Element Visibility via JavaScript
// http://perishablepress.com/press/2008/04/29/toggle-element-visibility-via-javascript/

function toggle(x) {
	if (document.getElementById(x).style.display == 'none') {
		document.getElementById(x).style.display = '';
	} else {
		document.getElementById(x).style.display = 'none';
	}
}
