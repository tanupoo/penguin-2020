/*
 * plod-listview.js
 */
function make_table_from_dict(d, header_list)
{
    let details = "";
    if (d.length > 0) {
        details += "<table><thead>";
        details += "<tr>";
        header_list.filter(x => x.list == true).forEach(x => details += `<th>${x.notation}</th>`);
        details += "</tr><tbody>";
        d.forEach(r => {
            details += "<tr>";
            header_list.filter(x => x.list == true).forEach(x => {
                var y = Object.entries(r).find(a => a[0] == x.key);
                if (y != undefined) {
                    details += "<td>" + y[1] + "</td>";
                } else {
                    details += "<td></td>";
                }
            });
            details += "</tr>";
        });
        details  += "</tbody></table>";
    }
    return details;
}

function make_details_view(row_data, delete_button_id)
{
    let details = "";
    details += "<hr>"
    details += `<div class="inline-block div-block"><label class="label">dateConfirmed</label><span class="value-box inset-box">${row_data.dateConfirmed}</span></div>`;
    details += make_table_from_dict(row_data.locationHistory, headers_PLH);
    details += make_table_from_dict(row_data.conditionHistory, headers_PCH);
    details += "<br>";
    details += `<div class="inline-block div-block"><label class="label">closeContacts</label><span class="value-box inset-box">${row_data.closeContacts}</span></div>`;
    details += "<hr>";
    details += `<div class="inline-block div-block"><label class="label">updatedTime</label><span class="value-box inset-box">${row_data.updatedTime}</span></div>`;
    details += `<div class="inline-block div-block"><label class="label">createdTime</label><span class="value-box inset-box">${row_data.createdTime}</span></div>`;

    if (delete_button_id) {
        details += `<div class="inine-block div-block">`
        details += `  <label class="label">_id</label>`
        details += `  <span class="value-box inset-box">${row_data._id}</span>`
        details += `  <span style="float:right; margin-right:5px"><input class="control-button notation" id="${delete_button_id}" type="button" value="削除する"></span>`
        details += `</div>`;
    }

    return details;
}

/*
 * parent_obj is a native object for the list view like document.getElementById("plod-list")
 * args may inlcude:
 *   enable_delete_button: boolean
 */
function plod_listview_init(parent_obj, args)
{
    /* create table of list view */
    let tr = document.createElement("tr");
    tr.appendChild(document.createElement("th"));   // this is for details-button()
    headers_base.filter(x => x.list == true).forEach(x => {
        var th = document.createElement("th");
        th.innerHTML = x.notation;
        tr.appendChild(th);
    });
    let thead = document.createElement("thead");
    thead.appendChild(tr);
    parent_obj.appendChild(thead);

    let columns = headers_base.filter(x => x.list == true).map(x => {
        return {
            "data": x.key,
            "orderable": x.orderable,
        };
    });
    columns.unshift({
        "className": "details-button",
        "orderable": false,
        "data": null,
        "defaultContent": "",
    });
    plod_table = $("#plod-list").DataTable( {
        "ajax": {
            "url": "/tummy/json/all",
            "dataSrc": "plod",
        },
        "columns": columns,
        "order": [[1, "asc"]],
    } );

    /*
     * You have to consider below two controls for clicking the row in the list view.
     */
    $("#plod-list tbody").on("click", "tr", function () {
        let tr = $(this).closest("tr");
        let row = plod_table.row( tr );
        /*
         * excute below only when the details in this row is NOT shown.
         * see the case in below where td.details-button is clicked.
         */
        if (! row.child.isShown()) {
            /*
             * close other rows showing details anyway.
             * and two ways;
             *   1. remove class "selected" from this row when the row has been selected.
             *   2. otherwise, add class "selected" in this row.
             */
            if (plod_table.row(".shown").length) {
                $(".details-button", plod_table.row(".shown").node()).click();
            }
            if ( $(this).hasClass("selected") ) {
                $(this).removeClass("selected");
            }
            else {
                plod_table.$("tr.selected").removeClass("selected");
                $(this).addClass("selected");
            }
        }
    } );

    /*
     * See above the clikcing "plod-list tbody" control.
     */
    $("#plod-list tbody").on("click", "td.details-button", function () {
        let tr = $(this).closest("tr");
        let row = plod_table.row( tr );
        /*
         * when you see the details in this row, it close the details.
         * and, remove classes; "shown" and "selected".
         * otherwise, it shows details AND adds the two classes after removing "selected" from all other rows..
         */
        if ( row.child.isShown() ) {
            /*
             * close this details because this row is already open.
             * remove classes; shown and selected.
             */
            row.child.hide();
            tr.removeClass("shown");
            if ($(this).hasClass("selected")) {
                $(this).removeClass("selected");
            }
        } else {
            // cloase other rows anyway.
            if (plod_table.row(".shown").length) {
                $(".details-button", plod_table.row(".shown").node()).click();
            }
            if (args.enable_delete_button == true) {
                delete_button_id = "button-delete-plod-" + Math.random().toString().slice(-8);
                row.child(make_details_view(row.data(), delete_button_id)).show();
                jQuery(`#${delete_button_id}`).on("click", function() {
                    if (true == confirm("削除しますか？")) {
                        let result = delete_plod(row.data()["reportId"]);
                    }
                    row.child.hide();
                    tr.removeClass("shown");
                    // XXX why it doesn't work ?
                    // XXX referring to https://datatables.net/examples/api/select_single_row.html
                    // row.remove().draw( false );
                    $(this).removeClass("selected");
                });
            } else {
                row.child(make_details_view(row.data())).show();
            }
            tr.addClass("shown");
            plod_table.$("tr.selected").removeClass("selected");
            tr.addClass("selected");
            // add event.
        }
    } );
}

