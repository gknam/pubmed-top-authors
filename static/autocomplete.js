// Get list of auto-suggestions
$(document).ready(function() {
    $("#form").submit(function() {
        $.getJSON("http://preview.ncbi.nlm.nih.gov/portal/utils/autocomp.fcgi?dict=pm_related_queries_2&callback=?&q="
                + encodeURIComponent($("#q").val()), NSuggest_CreateData);
        return false;
    });
});

function NSuggest_CreateData(q, data) {
    var ul = $("#results");
    ul.empty();
    $.each(data, function(i, text) {
        ul.append($("<li/>").text(text));
    });
}
