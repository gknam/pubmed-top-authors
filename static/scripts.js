// Execute when the DOM is fully loaded
$(function() {

    // configure typeahead
    $("#q").typeahead({
        highlight: false,
        minLength: 1
    }, {
        display: function(suggestion) {
            return null;
        },
        limit: 10,
        source: suggest,
        templates: {
            suggestion: Handlebars.compile(
                "<div>" +
                "{{suggestion}}" +
                "</div>"
            )
        }
    });

    // fetch records for the term selected from drop-down
    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {

        records(suggestion);

    });
});


/**
 * fetches suggestions from Pubmed API
 */
function suggest(query, syncResults, asyncResults) {
    // get places matching query (asynchronously)
    var parameters = {
        q: query
    };


    // Cancel previous request after new request is made (http://stackoverflow.com/a/12713532)
    if (typeof request !== "undefined") {
        request.abort()
    }

    // get list of suggestions
    request = // if "var request" is used, "request.abort()" does not work.
        $.getJSON(Flask.url_for("suggest"), parameters)
        .done(function(data, textStatus, jqXHR) {

            // call typeahead's callback with suggest results (i.e. terms)
            asyncResults(data);
        })
        .fail(function(jqXHR, textStatus, errorThrown) {

            // log error to browser's console
            console.log(errorThrown.toString());

            // call typeahead's callback with no results
            asyncResults([]);
        });
}




/**
 * Updates UI's markers.
 */
function records(suggestion) {

    var parameters = {
        term: suggestion.suggestion
    };

    $.getJSON(Flask.url_for("records"), parameters)
        .done(function(data, textStatus, jqXHR) {

            // // start content
            // content = "<div><ul>";

            // // add records to marker
            // for (var i = 0; i < data.length; i++)
            // {
            //     content += "<li><a href=\"";
            //     content += data[i].link;
            //     content += "\" target=\"_blank\">";
            //     content += data[i].title;
            //     content += "</a></li>";
            // }

            // // end content
            // content += "</ul></div>";

            console.log(data);
        })

    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });
}

// Notes for myself: "request.abort()" does not work if "var request" is used instead of just "request" for "$.getJSON".