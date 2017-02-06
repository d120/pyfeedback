function create_csv_table(div_context, tutoren_csv_content) {
    if(div_context === undefined || div_context == null || div_context.length == 0) return false;
    if(tutoren_csv_content === undefined || tutoren_csv_content == null) return false;

    var csv = tutoren_csv_content;
    div_context.empty();

    var table_elem = $("<table>").appendTo(div_context);

    var column_names = ["Num", "Nachname", "Vorname", "E-Mail", "Bemerkung"];

    var csv_lines = csv.split("\n");

    var head_row = $("<tr>").appendTo(table_elem);
    for(var column_key = 0; column_key < column_names.length; column_key++) {
        $("<th>").text(column_names[column_key]).appendTo(head_row);
    }

    $.each(csv_lines, function(key, value) {
        if(value == "") return true;
        var row_items = value.split(",");
        var count_csv_columns = row_items.length;
        if(count_csv_columns > 4) {
            div_context.html('<p class="p_error_csv">CSV Fehlerhaft: ' +
                    'Bei min. einem Tutor mehr als 4 Spalten eingefügt</p>')
            return false;
        }
        var new_row = $("<tr>");
        $("<td>").text(key+1).appendTo(new_row);
        var i = 0;
        for(;i < count_csv_columns; i++) {
            $("<td>").text(row_items[i]).appendTo(new_row);
        }
        for(; i <= 4;i++) {
            $("<td>").appendTo(new_row);
        }
        new_row.appendTo(table_elem);
    });

    return false;
}