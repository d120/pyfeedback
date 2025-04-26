function check_checkboxes(event, checked) {
    var parentElem = $(event.target).parent().parent();

    var checkboxes;
    if (checked) {
        checkboxes = parentElem.find(".attended_course > input:checkbox");
        var unattended_courses = parentElem.find(".unattended_course");
        if (unattended_courses.length > 0) {
            alert("Es gibt Veranstaltungen ohne validen Dozenten. Diese Veranstaltungen wurden nicht ausgewählt.");

            var expandParent = function (childElem) {
                var accordeon_div = childElem.parent().parent();
                var accordeon_title = accordeon_div.prev();
                if (accordeon_title.is("h3")) {
                    if (!accordeon_div.is(":visible")) { // only expand if collapsed
                        accordeon_title.click();
                    }
                    expandParent(accordeon_title);
                }
            }
            expandParent(unattended_courses.eq(0))
        }
    } else {
        checkboxes = parentElem.find("input:checkbox");
    }
    checkboxes.prop('checked', checked);
    event.preventDefault();
}


$(function () {
    $(".accordion").accordion({ heightStyle: "content", collapsible: true, active: false });

    $("a.markall").click(function (event) { check_checkboxes(event, true); });
    $("a.unmarkall").click(function (event) { check_checkboxes(event, false); });
});


window.onload = () => {
    let regex = /\(20-[0-9]{2}-.*\)/;
    let labels = [...document.querySelectorAll("label")].filter(lb => regex.test(lb.innerText));

    let li = labels.map(label => label.parentElement);

    let li_attended = li.filter(l => l.classList.contains("attended_course"));
    let li_unattended = li.filter(l => l.classList.contains("unattended_course"));

    if (li_attended.length > 0) {
        let checkboxes = li_attended.map(l => l.querySelector('input[type="checkbox"]'));
        checkboxes.forEach(c => c.checked = true);
    }

    if (li_unattended.length > 0) {
        alert(`There are ${li_unattended.length} courses that were not automatically selected in FB20`);
    }
}