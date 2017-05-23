 // search term// Execute when the DOM is fully loaded
$(function() {

    // configure typeahead
    $("#q").typeahead({
        highlight: false,
        minLength: 1
    }, {
        display: function(suggestion) {
            return null; // See Note 2 at the bottom about what to display.
        },
        limit: 10,
        source: suggest,
        templates: {
            suggestion: Handlebars.compile(
                "<div>" +
                "{{term}}" +
                "</div>"
            )
        }
    });

    // fetch records for the term selected from drop-down
    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {
        $("#q").typeahead('destroy'); // remove drop-down
        $("#q").focus(); // place cursor in textbox
        records(suggestion);

    });
});


/**
 * fetches suggestions from Pubmed API
 */
function suggest(query, syncResults, asyncResults) {
    // get places matching query (asynchronously)
    var parameters = {
        q: query // search term
    };


    // Cancel previous request after new request is made (http://stackoverflow.com/a/12713532)
    if (typeof request !== "undefined") {
        request.abort();
    }

    // get list of suggestions
    request = // See "Note 1" at the bottom
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
        term: suggestion.term
    };

    $.getJSON(Flask.url_for("records"), parameters)
        .done(function(data, textStatus, jqXHR) {

            drawGraphs(data);
        })

    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });
}

function drawGraphs(data) {
    // Width and height
    var w = 500;
    var h = 100;

    // Data
    var dataset = [5, 10, 15, 20, 25];

    for (i of dataset) {
        console.log(i);
    }

    // Create SVG element
    var svg = d3.select("body")
        .append("svg")
        .attr("width", w)
        .attr("height", h);

    // Create reference to all circles (one circle per data point)
    var circles = svg.selectAll("circle")
        .data(dataset)
        .enter()
        .append("circle");

    // Create circles
    circles.attr("cx", function(d, i) {
            return (i * 70) + 25;
        })
        .attr("cy", h / 2)
        .attr("r", function(d) {
            return d;
        })
        .attr("fill", function(d) {
            if (d < 15) {
                return "black";
            } else if (d < 25) {
                return "purple";
            } else {
                return "red";
            }
        })
        .attr("stroke", "orange")
        .attr("stroke-width", function(d) {
            return d / 2;
        });


}


/*
Note 1
"request.abort()" does not work if "var request" is used instead of just
"request" for "$.getJSON".

To check if the abort has been made, add the following line under "request.abort()".

console.log(request.statusText);

The abort status could also be checked at Chrome's DevTools --> "Network" tab
--> "Status" column.

The ".abort()" method does not work with "jsonP". Check the following page for an explanation with alternative method.
http://stackoverflow.com/a/9999813

Note 2
Code examples:

1. Display nothing ("null" can be replaced with any desired value.)

    Method 1 
    display: function(suggestion) {
                return null;
            }
    
    Method 2
    display: function(){return null}


2. Display the selected value

    Method 1
    display: function(suggestion) {
                return suggestion.term;
            }

    Method 2
    display: "term"


*/


