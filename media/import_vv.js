function expandParent(childElem) {
    let accordeon_div = childElem.parent().parent();
    let accordeon_title = accordeon_div.prev();
    if (accordeon_title.is("h3")) {
        if (!accordeon_div.is(":visible")) { // only expand if collapsed
            accordeon_title.click();
        }
        expandParent(accordeon_title);
    }
}

let REGEX = /\(20-[0-9]{2}-.*\)/;

function alertDeciderFB20(checkbox) {
    let li = checkbox.parent();

    if ((!REGEX.test(li.find("label").text())) && checkbox.is(':checked')) {
        return true; // alert!
    }
    return false;
}

function clickHandler(event) {
    let cb = $(event.target);
    if (alertDeciderFB20(cb)) {
        alert("You have choosen a course that is not in FB20!")
    }
}

function markAllHandler(checkboxes) {
    let count = 0;

    for (const cb of checkboxes) {
        if (alertDeciderFB20($(cb))){
            count++;
        }
    }
    
    if (count > 0) {
        alert(`You have choosen ${count} courses that are not in FB20!`)
    }
}

function check_checkboxes(event, checked) {
    let parentElem = $(event.target).parent().parent();

    let checkboxes;
    if (checked) {
        checkboxes = parentElem.find(".attended_course > input:checkbox");
        let unattended_courses = parentElem.find(".unattended_course");
        if (unattended_courses.length > 0) {
            alert(`Es gibt ${unattended_courses.length} Veranstaltungen ohne validen Dozenten. Diese Veranstaltungen wurden nicht ausgewählt.`);
            expandParent(unattended_courses.eq(0));
        }
    } else {
        checkboxes = parentElem.find("input:checkbox");
    }
    checkboxes.prop('checked', checked);

    if (checked) {
        markAllHandler(checkboxes);
    }

    event.preventDefault();
}

$(function () {
    $(".accordion").accordion({ heightStyle: "content", collapsible: true, active: false });

    $("a.markall").on('click', function (event) { check_checkboxes(event, true); });
    $("a.unmarkall").on('click', function (event) { check_checkboxes(event, false); });
    $("input.checkbox").on('change', function (event) { clickHandler(event); });
});

window.onload = () => {
    let labels = [...document.querySelectorAll("label")].filter(lb => REGEX.test(lb.innerText));

    let li = labels.map(label => label.parentElement);

    let li_attended = li.filter(l => l.classList.contains("attended_course"));
    let li_unattended = li.filter(l => l.classList.contains("unattended_course"));

    if (li_attended.length > 0) {
        let checkboxes = li_attended.map(l => l.querySelector('input[type="checkbox"]'));
        checkboxes.forEach(c => c.checked = true);
    }

    if (li_unattended.length > 0) {
        // if run immediately it does expand as expected, as page is still loading at this point
        setTimeout(() => {
            alert(`There are ${li_unattended.length} courses that were not automatically selected in FB20`);
            expandParent($(li_unattended).eq(0));
        }, 100);
    }
}