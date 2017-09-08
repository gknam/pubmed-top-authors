// Execute when the DOM is fully loaded
$(function() {

    // set up dialog boxes for "About" and "Contact" links
    setUpDialog("#about", "#dialog_about", "About")
    setUpDialog("#contact", "#dialog_contact", "Contact")

    // configure typeahead
    function typeAhead() {
        $("#q").focus();

        $("#q").typeahead({
            highlight: false,
            minLength: 1
        }, {
            display: function(suggestion) {
                return null; // See "Note 3" at the bottom about what to display.
            },
            limit: 20,
            source: suggest,
            templates: {
                suggestion: Handlebars.compile(
                    "<div>" +
                    "{{term}}" +
                    "</div>"
                )
            }
        });
    }

/* This block handles tab key press in input "#q" better, but there are caveats. Therefore this has been discarded for now.
The working part is that when tab is pressed, focus moves to 'fetch' button while leaving typed value as it is.
The problems are that "shift + tab" does nothing, and when pressed many times, the focus moves to previous input boxes
(as intended), but when users "tab" forward into input "#q" and "tab" again, the typed value gets lost.

function handleTabPress(inputId) {
    var inputVal;
    var keys = {9: false, 16: false};

    // handle tab press
    $(".form-group").on('keydown', inputId, function(e) { 
        if (e.keyCode in keys) {
            keys[e.keyCode] = true;            
        }
        console.log(keys);

        // var keyCode = e.keyCode || e.which;
        if (keys[9] && !keys[16]) { 
            console.log("fire")
            // console.log(inputVal);
            // $(inputId).val(inputVal);
            // var e = jQuery.Event("keydown");
            // e.which = 9;
            // $(inputId).trigger(e);
            $(inputId).typeahead('destroy'); // remove drop-down
            typeAhead();
            $(inputId).typeahead('val', inputVal);
            $('#fetch').focus();
        }
    });

    // remember input values
    $(".form-group").on('keyup', inputId, function(e) { 
        if (e.keyCode in keys) {
            keys[e.keyCode] = false;
        }

        if (!keys[9]) {
            inputVal = $(this).val();
            // console.log(inputVal);
            console.log(keys);
        }
    });

};

handleTabPress("#q");
*/

    function handleInput() {

        // fetch records for the term selected from drop-down
        $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {
            fetch(suggestion, null);
        });

        // fetch records for the term typed in the form if enter key is pressed
        $("form").submit(function(e) {
            fetch(this, e);
        });

        // do not fetch, but only autocomplete search term if tab key is pressed
        $("#q").on("typeahead:autocomplete", function(eventObject, suggestion, name) {
            $("#q").val(suggestion.term);
        });


        function fetch(termContainer, e) {

            /* get search parameters */

            var term;
            var articles;
            var days;

            // typeahead selection
            if (!e) {
                term = termContainer.term;
                articles = $("#a").val();
                days = $("#d").val();
            }
            // submission by pressing enter
            else {
                term = termContainer.q.value;
                articles = termContainer.a.value;
                days = termContainer.d.value;

                // do nothing if
                // (1) term is empty (enter was pressed without typing a term) or
                // (2) contains only white spaces (code from https://stackoverflow.com/a/10262019/7194743)
                if (term == '' || !term.replace(/\s/g, '').length) {
                    e.preventDefault();
                    return;
                }
            }

            suggestion = {
                "term": term,
                "retmax": articles,
                "reldate": days
            };

            // remove drop-down
            $("#q").typeahead('destroy');

            $("form").trigger("reset"); // this line is necessary if submissionType is "submissionByEnter" (without this, the suggestions list reappears immediately)
            $("#a").val(articles);
            $("#d").val(days);
            typeAhead();
            $("#q").focus();
            $("svg").remove();
            $("." + barDialog_div).remove();

            if (e) {
                e.preventDefault();
            }

            resetDisplay(searchTerm_div, images_div, pl1Svg_div, pl23Svg_div);
            displaySearchTerm(searchTerm_div, suggestion.term.toLowerCase());
            displayGif(images_div, loadingGif); // See Note 6 at the bottom.
            records(suggestion);
        }
    }

    typeAhead();
    handleInput();

});

// classes for SVGs and DIVs
var pl1Svg_class = "author";
var pl2Svg_class = "year";
var pl3Svg_class = "journal";

var searchTerm_div = "searchTerm";
var images_div = "images"; // for "loadingGif" or apologies images
var pl1Svg_div = "authorDiv";
var pl23Svg_div = "yearJournalDiv";
var barDialog_div = "dialog_bar"

// to be set in "chartDim" function
var wToSratio;
var svgMaxWidth;

// load GIF image to display after submitting keyword
var loadingGif = new Image();
loadingGif.alt = "loading";
loadingGif.src = "/static/loading.gif";

// load image to display when keyword fetched no data
var imageUrl = "http://i.imgur.com/A3ZR65I.png";
// data fetch problem 1: empty data received
var apology1 = apologyImage("no records found", "no records found", "try_a_different_keyword", imageUrl)

// data fetch problem 2: error message received
var apology2 = apologyImage("error", "error", "try_again", imageUrl)

// data fetch problem 3: no data received (server may be offline)
var apology3 = apologyImage("record fetching failed", "record_fetching_failed. server may be offline", "try_again", imageUrl)

function apologyImage(altText, topText, bottomText, imageUrl) {
    var apology = new Image();
    apology.alt = altText;
    var topText = topText;
    var bottomText = bottomText;
    apology.src = "https://memegen.link/custom/" + topText + "/" + bottomText + ".jpg?alt=" + imageUrl;
    return apology;
}

function changeSvgViewboxDim(vb_xMin, vb_YMin, vb_width, vb_height, svgClass) {
    // change all SVGs unless one is specified
    var svgToAdjust = 'svg';

    if (svgClass != null) {
        var svgToAdjust = svgClass;
    }

    // note new viewBox values
    var vbArray_new = [];

    for (var i = 0; i < 4; i++) {
        vbArray_new.push(arguments[i]);
    }

    // console.log("arguments[0] = " + arguments[0]);
    // console.log("arguments[1] = " + arguments[1]);
    // console.log("arguments[2] = " + arguments[2]);
    // console.log("arguments[3] = " + arguments[3]);
    // console.log("arguments[4] = " + arguments[4]);
    // console.log("vb_xMin: " + vb_xMin);
    // console.log("vb_YMin: " + vb_YMin);
    // console.log("vb_width: " + vb_width);
    // console.log("vb_height: " + vb_height);
    // console.log("svgClass: " + svgClass);

    // code from https://stackoverflow.com/a/24913841/7194743
    $(svgToAdjust).each(function () {
        // code from https://stackoverflow.com/a/7682976/7194743
        // get viewBox values
        var vb = $(this)[0].getAttribute('viewBox');
        var vbArray_current = vb.split(/\s+|,/);

        // change viewBox values if new values have been given as input
        for (var i in vbArray_current) {
            if (vbArray_new[i] != null) {
                // console.log("arguments[" + i + "]: " + arguments[i]);
                // console.log("arguments[" + i + "] = " + arguments[i]);
                vbArray_current[i] = vbArray_new[i].toString();
            }
        }
        new_vb = vbArray_current.join(' ');

        $(this).removeAttr('viewBox');
        $(this)[0].setAttribute('viewBox', new_vb);
    });
}

function displaySearchTerm(divClass, searchTerm) {
    $("." + divClass).css("justify-content", "center");
    $("." + divClass).css("display", "flex");
    $("." + divClass).css("text-align", "justify");
    $("." + divClass).css("font-size", "30px");
    $("." + divClass).append("Search term: " + searchTerm);
}

function displayGif(divClass, loadingGif) {
    $("." + divClass).css("justify-content", "center");
    $("." + divClass).css("display", "flex");
    $("." + divClass).append(loadingGif);
}

function resetDisplay(divClass1, divClass2, divClass3, divClass4) {
    for (i of arguments) {
        $("." + i).empty();
        $("." + i).removeAttr("style");
    }
}

function setUpDialog(linkId, dialogId, dialogTitle) {
    // set up dialog box for link (code based on http://jsfiddle.net/kwalser/ymssceqv/)
    $(dialogId).dialog({
        autoOpen: false,
        autoResize: true,
        modal: true,
        title: dialogTitle,
        height: "auto", // code from https://stackoverflow.com/a/764857/7194743
        width: "auto"
        // If width and height are to be specified, see https://stackoverflow.com/a/12537610/7194743
    })
    // change title bar close button icon
    // (code based on https://stackoverflow.com/a/21337337/7194743 and https://stackoverflow.com/a/7910817/7194743)
    .prev(".ui-dialog-titlebar")
    .find(".ui-button-icon")
    .switchClass("ui-icon-closethick", "ui-icon-circle-close"); // Note jQuery UI requires no "." to precede class names.

    // enable dialogue for link (code based on https://stackoverflow.com/a/964507/7194743)
    if (linkId) {
        $(linkId).click(function() {
            $(dialogId).dialog("open");
        });
    }
}

function dataFetchProblem(data) {
    var apology;

    // no data received (server may be offline)
    if (data == null) {
        apology = apology3;
    }

    else {
        var data_keys = Object.keys(data);
        var dc_i = data_keys.indexOf("dataCount");
        data_keys.splice(dc_i, 1);
        var dslm_i = data_keys.indexOf("dataStrLengthMax");
        data_keys.splice(dslm_i, 1);

        // empty data received
        if (data_keys.length == 0) {
            apology = apology1;
        }
        // error message received
        else if (data == "error") {
            apology = apology2;
        }
    }
    
    return apology;
}

function apologise(divClass, apology) {

    // display image
    $("." + divClass).css("justify-content", "center");
    $("." + divClass).css("display", "flex");
    $("." + divClass).css("text-align", "justify");
    $("." + divClass).append(apology);
}

/**
 * fetches suggestions from Pubmed API
 */
function suggest(query, syncResults, asyncResults) {
    // get places matching query (asynchronously)
    var parameters = {
        q: query.toLowerCase() // search term
    };


    // initiate suggestions list
    matches_dic = [];

    // get list of suggestions
    $.getJSON("https://www.ncbi.nlm.nih.gov/portal/utils/autocomp.fcgi?dict=pm_related_queries_2&callback=?", parameters, NSuggest_CreateData)
        .always(function(data, textStatus, jqXHR) { // See "Note 1" at the bottom about not including ".done"
            asyncResults(matches_dic);

        });


    // See "Note 2" at the bottom about cancelling ".getJSON" request.

}




/**
 * Updates UI's markers.
 */

function records(suggestion) {

    var parameters = {
        term: suggestion.term,
        retmax: suggestion.retmax,
        reldate: suggestion.reldate
    };

    // Cancel previous request after new request is made (http://stackoverflow.com/a/12713532)
    if (typeof request !== "undefined") {
        request.abort();
    }


    // fetch records
    request =
        $.getJSON(Flask.url_for("records"), parameters)
        .done(function(data, textStatus, jqXHR) {
            // remove GIF (See "Note 5" at the bottom)
            resetDisplay(images_div);

            // prepare apology if data is empty has failed
            apology = dataFetchProblem(data);

            // display apology message if there was a problem fetching data
            if (apology) {
                apologise(images_div, apology);
            }
            
            // otherwise, draw plots
            else {
                drawGraphs(data, suggestion.term);
            }
        })

        .fail(function(jqXHR, textStatus, errorThrown) {

            // log error to browser's console
            console.log(errorThrown.toString());

            // remove GIF
            resetDisplay(images_div);

            // display apology message
            apology = dataFetchProblem(null);
            apologise(images_div, apology);

        });
}

function NSuggest_CreateData(q, matches, count) {
    matches_dic = [];
    for (var i of matches) {
        matches_dic.push({ "term": i });
    }

    return matches_dic;
}

function swapNamePositions (plotData) {
    var lName = plotData.au.split(", ")[0];
    var fName = plotData.au.split(", ")[1];
    return fName + " " + lName;
}

function dialogsForPlots(svgClass, plotData) {
    // code from http://bl.ocks.org/jfreels/6735318
    if (svgClass != pl1Svg_class) {
        var body = d3.select('body')
            .selectAll('div')
            .data(plotData, function (d, i) {
                var output;
                if (typeof(d) == "undefined") {
                    output = (function() {return})()
                }
                else {
                    // console.log(d.barId);
                    output = d.barId;
                }

                return output; 
            })
            .enter()
            .append('div')
                .attr('class', barDialog_div)
                .attr('id', function (d) {
                        return d.barId + "_dialog";
                })
                .style("display", "none")
                .html(function (d, i) {
                    var list = "<ul>";
                    for (k of d.ref) {
                        // no publication record
                        if (k[0] == null) {
                            list += "<li>No publications to display</li>"
                            refYear = (parseInt(refYear) + 1).toString();
                            break;
                        }

                        refYear = k[1];

                        // author names, year, article title, jounral title, journal volume
                        list += "<li>" + k[0] + "(" + refYear + "). " + k[2] + " <i>" + k[3] + ", " + k[4] + "</i>"
                        
                        // journal issue
                        if (k[5] != "") {
                            list += "(" + k[5] + "), ";
                        }
                        else {
                            list += ", ";
                        }

                        // Pubmed link
                        list += k[6] + ". <a href=\"" + k[7] + "\" target=\"_blank\">Pubmed</a>"

                        // DOI link
                        if (k[8] != "") {
                            list += " <a href=\"" + k[8] + "\" target=\"_blank\">DOI</a></li>";
                        }
                        else {}
                    }
                    list += "</ul>"


                    var category = (function () {
                        if (svgClass == pl2Svg_class) {
                            return refYear;
                        }
                        else if (svgClass == pl3Svg_class) {
                            return k[3];
                        }
                    })();

                    var dialogTitle = swapNamePositions(plotData[i]) + '\'s publications in ' + category;
                    var dialogId = "#" + d.barId + "_dialog";
                    setUpDialog(null, dialogId, dialogTitle);

                    return list;
                });
    }
}

function drawGraphs(data, term) { // term will be passed to drawBarChart

    // Create SVG element
    var pl1Svg = insertSVG(pl1Svg_class, pl1Svg_div);
    var pl2Svg = insertSVG(pl2Svg_class, pl23Svg_div);
    var pl3Svg = insertSVG(pl3Svg_class, pl23Svg_div);

    // dimension for chart within SVG
    var pl1Dim;
    var pl2Dim;
    var pl3Dim;

    // d3.select("body")
    //     .append("svg")
    //     .attr("width", width + marginLeft + marginRight)
    //     .attr("height", height + marginTop + marginBottom)
    //     .attr("class", "pl1")
    //     .attr("shape-rendering", "crispEdges"),
    //     pl2Svg = d3.select("body")
    //     .append("svg")
    //     .attr("width", width + marginLeft + marginRight)
    //     .attr("height", height + marginTop + marginBottom)
    //     .attr("class", "pl2")
    //     .attr("shape-rendering", "crispEdges"),
    //     pl3Svg = d3.select("body")
    //     .append("svg")
    //     .attr("width", width + marginLeft + marginRight)
    //     .attr("height", height + marginTop + marginBottom)
    //     .attr("class", "pl3")
    //     .attr("shape-rendering", "crispEdges");

    // data for each plot
    var pl1 = []; // authors (x-axis) and number of publications (y-axis)
    var pl2 = []; // years (x-axis) and number of publications (y-axis)
    var pl3 = []; // journals (x-axis) and number of publications (y-axis)

    // number of data points in each plot
    var auCount = 0;
    var yearCount = 0;
    var journalCount = 0;

    // for determining the left margin of SVG
    var auStrLengthMax = 0;
    var yearStrLengthMax = 0;
    var journalStrLengthMax = 0;

    // get max string length among author names, journal names and years
    // this will be the left margin of all plots
    var authorStrLenMax = data.dataStrLengthMax.authorStrLenMax;
    var journalStrLenMax = data.dataStrLengthMax.journalStrLenMax;
    var yearStrLenMax = data.dataStrLengthMax.yearStrLenMax;

    var allStrLenMax = Math.max(authorStrLenMax, journalStrLenMax, yearStrLenMax);

    // max data counts --> consider removing these as these are not being used
    var authorCountMax = data.dataCount.authorCountMax;
    var journalCountMax = data.dataCount.journalCountMax;
    var yearCountMax = data.dataCount.yearCountMax;


    // process data and draw plots 2 and 3
    // each author
    var auIdList = [];

    for (var i in data) {

        // skip max plot dimensions info
        if (i == "dataCount" || i == "dataStrLengthMax") {}

        // process publication records
        else {
            
            for (var j of data[i]) {

                // each author
                for (var au in j) {

                    // plot 1
                    var auPubs = parseInt(j[au][0]["total"]);

                    auCount += 1;

                    if (au.length >= auStrLengthMax) {
                        auStrLengthMax = au.length;
                    }

                    // for displaying plots 2 and 3 (author's publications)
                    // on bar-click in plot 1 (one bar per author)
                    var auId = "au" + auCount.toString();
                    auIdList.push(auId);

                    pl1.push({
                        "x": auPubs, // publications count for author\
                        "y": au, // author
                        "barId": auId
                    });

                    // plot 2 (one plot per author)
                    var yRec = j[au][2]["years"];
                    var years = Object.keys(yRec);
                    var yearPubs = [];
                    var yearRefs = [];
                    for (i of Object.values(yRec)) {
                        yearPubs.push(i[0]);
                        yearRefs.push(i[1]);
                    };
                    // console.log(yearPubs[0]);
                    // console.log(yearRefs[0]);

                    var yearIdList = [];
                    var yearPubsAll = [];

                    for (var year in years) {

                        yearCount += 1;

                        if (years[year].length >= yearStrLengthMax) {
                            yearStrLengthMax = years[year].length;
                        }

                        if (!(yearPubsAll.includes(yearPubs[year]))) {
                            yearPubsAll.push(yearPubs[year]);
                        }

                        // for displaying dialog box of references
                        // on bar- or circle-click (one bar or circle per year)
                        var yearId = auId + "_year" + yearCount.toString();
                        yearIdList.push(yearId);

                        pl2.push({
                            "x": years[year],
                            "y": yearPubs[year],
                            "au": au,
                            "barId": yearId,
                            "ref": yearRefs[year]
                        });

                    }

                    if (yearCount === 1) {
                        pl2[0].y = [pl2[0].x, pl2[0].x = pl2[0].y][0]; // swap x and y value (https://stackoverflow.com/a/16201730)
                        pl2Dim = chartDim(pl2Svg, yearCount, null, allStrLenMax);
                        drawBarChart(pl2Svg_class, pl2Svg, pl2, auId, pl2Dim, "hidden", "barChartAxis", term);
                    }
                    else if (yearCount > 1) {
                        pl2Dim = chartDim(pl2Svg, yearCount, yearPubsAll.length, allStrLenMax);
                        drawLineChart(pl2Svg_class, pl2Svg, pl2, auId, pl2Dim, "hidden", "lineChartAxis", term);
                    }

                    pl2 = [];
                    yearCount = 0;
                    yearStrLengthMax = 0;
                    yearPubsAll = []; // this may be a repetition?

                    // plot 3 (one plot per author)
                    var jRec = j[au][1]["journals"];
                    var journals = Object.keys(jRec);
                    var journalPubs = [];
                    var journalRefs = [];
                    for (i of Object.values(jRec)) {
                        journalPubs.push(i[0]);
                        journalRefs.push(i[1]);
                    };


                    var journalIdList = [];

                    for (var journal in journals) {

                        journalCount += 1;

                        if (journals[journal].length >= journalStrLengthMax) {
                            journalStrLengthMax = journals[journal].length;
                        }

                        // for displaying dialog box of references
                        // on bar- or circle-click (one bar or circle per year)
                        var journalId = auId + "_journal" + journalCount.toString();
                        journalIdList.push(journalId);

                        pl3.push({
                            "x": journalPubs[journal], // publication count per year
                            "y": journals[journal],
                            "au": au,
                            "barId": journalId,
                            "ref": journalRefs[journal]
                        });

                    }

                    pl3Dim = chartDim(pl3Svg, journalCount, null, allStrLenMax);

                    drawBarChart(pl3Svg_class, pl3Svg, pl3, auId, pl3Dim, "hidden", "barChartAxis");
                    pl3 = [];
                    journalCount = 0;
                    journalStrLengthMax = 0;
                }
            }
        }
    }


    // plot 1
    pl1Dim = chartDim(pl1Svg, auCount, null, allStrLenMax);
    drawBarChart(pl1Svg_class, pl1Svg, pl1, "pl1Chart", pl1Dim, "visible", "barChartAxis", term);

    // change SVG viewBox width (which is currently 0)
    changeSvgViewboxDim(null, null, vb_width = svgMaxWidth, null, null);

    function insertSVG(svgClass, divClass, divTitle = null) {
        return d3.select('.' + divClass)
                .append("svg")
                .attr("class", svgClass)
                .attr("shape-rendering", "auto")
                .attr("width", "100%")
                .attr("height", "100%") // will be adjusted in chartDim
                .attr("viewBox", "0 0 0 0")
                .attr("preserveAspectRatio", "xMinYMin");
    }

    function chartDim(svgElement, dataCount, dataValuesCount, dataStrLengthMax) {

        // get SVG's dimensions.
        // When SVG's width is set at "100%", the '.attr("width")' method returns "100%" whereas '.width()' returns the actual value.
        // Unfortunately, "svgElement.width()" does not work because it is a "DOM element not a jquery object" according to https://stackoverflow.com/a/34594058/7194743
        // The solution from the same web page is to use "each", as shown below.
        var svgElementWidth;
        var svgElementHeight;

        svgElement.each(function () {
            svgElementWidth = $(this).width();
        });


        svgElement.each(function () {
            svgElementHeight = $(this).height();
        });


        // windowWidth: screenWidth ratio for scaling down
        wToSratio = $(window).width() / screen.width;

        // SVG heights for plots 1 and 3 (made by "drawBarChart") depends on data (numbers of authors and journals)
        var svgHeight_temp = dataCount * 40;

        var marginTop_temp = dataCount;
        var marginBottom_temp = marginTop_temp;
        var height_temp = (svgHeight_temp - marginTop_temp - marginBottom_temp) * wToSratio;
        var barHeight = ((height_temp / dataCount) * 0.7 <= 35) ? (height_temp / dataCount) * 0.7 : 35;
        var fontSize = barHeight * 0.75;
        var barPadding = barHeight * 0.1; // this corresponds to 0.9 specified in barHeight.
        var marginLeft = dataStrLengthMax * fontSize / 3.5 + fontSize;
        var marginRight = fontSize;
        var width = svgElementWidth - marginLeft - marginRight;

        // ensure top and bottom margins are big enough for text
        var marginTop = fontSize * 2;
        var marginBottom = marginTop;
        
        // plot height
        var height = (barHeight + barPadding) * dataCount;

        // update height-related parameters
        var svgHeight_current = (svgElementHeight) * wToSratio;
        var svgHeight_new;

        if (dataValuesCount == null) { // for plot 3

            // set SVG height, ensuring it accommodates biggest chart
            svgHeight_new = height + marginTop + marginBottom;
            // console.log(svgElement.attr("class") + ": " + svgHeight_current + ", " + svgHeight_new);
            var svgHeight_chosen = svgHeight_current > svgHeight_new ? svgHeight_current : svgHeight_new;
            // console.log("svgHeight_current: " + (svgHeight_current * wToSratio) + "; svgHeight_new: " + (svgHeight_new * wToSratio));

            // if (svgElement.attr("class") == pl1Svg_class) {
            //     console.log(svgElement.attr("class") + ',' + dataCount + ',' + svgHeight_current);
            // }


            // if (svgElement.attr("class") == pl3Svg_class) {
            //     console.log(svgElement.attr("class") + ',' + dataCount + ',' + svgHeight_current);
            // }            
        }
        else { // for plot 2's line graph
            // console.log(svgElement.attr("class") + ": " + "testNotNull");
            // set SVG height for first graph
            var svgHeight_temp2 = dataValuesCount * 50 + marginTop + marginBottom;

            // update height-related parameters again
            marginTop_temp = dataValuesCount * 5;
            marginBottom_temp = marginTop_temp;
            height_temp = (svgHeight_temp2 - marginTop - marginBottom) * wToSratio;
            barHeight = ((height_temp / dataValuesCount) * 0.7 <= 35) ? (height_temp / dataValuesCount) * 0.7 : 35;
            barPadding = barHeight * 0.1; // this corresponds to 0.9 specified in barHeight.

            // plot height
            height = (barHeight + barPadding) * dataValuesCount;

            // update SVG height so that it accommodates biggest chart
            svgHeight_new = height + marginTop + marginBottom * 3;
            var svgHeight_chosen = svgHeight_current > svgHeight_new ? svgHeight_current : svgHeight_new;
        }
        svgMaxWidth = $("body").prop("clientWidth"); // code from https://stackoverflow.com/a/8340177
        svgElement.attr("viewBox", "0 0 0 " + (svgHeight_chosen));

        // svgElement.attr("height", function() {
        //     if (dataValuesCount == null) {
        //         return parseInt(svgHeight_current) + (fontSize * 2);
        //     } else {
        //         return dataValuesCount * 40 + (fontSize * 2);
        //     }
        // });



        return {
            width: width,
            height: height,

            marginTop: marginTop,
            marginBottom: marginBottom,
            marginLeft: marginLeft,
            marginRight: marginRight,

            barHeight: barHeight,
            barPadding: barPadding,

            fontSize: fontSize,

            dataCount: dataCount,
            dataValuesCount: dataValuesCount
        }
    }

    function drawBarChart(svgClass, svgElement, plotData, auId = null, chartDim, visibility, xAxisClass, term = null) {

        var width = chartDim.width;
        var height = chartDim.height;
        var barHeight = chartDim.barHeight;
        var barPadding = chartDim.barPadding;
        var marginTop = chartDim.marginTop;
        var marginLeft = chartDim.marginLeft;
        var fontSize = chartDim.fontSize;
        var dataCount = chartDim.dataCount;

        var barColour_unclicked = "#e600e6"
        var barColour_clicked = "green"

        // quit if no data
        if (dataCount == 0) {
            return;
        }

        // determine number of ticks on X-axis (number of publications)
        var xAxis_max = d3.max(plotData, function(d) {
            // console.log(svgClass);
            // console.log(d);
            return d.x;
        });

        var xTicks;

        if (xAxis_max % 5 > 0) {
            xTicks = xAxis_max + 5 - (xAxis_max % 5);
        } else {
            xTicks = xAxis_max;
        }



        // scales
        /*    var yScale = d3.scaleLinear()
                .domain([0, plotData.length])
                .range([sideP, width - sideP]);*/

        var xScale = d3.scaleLinear()
            .domain([0, xAxis_max])
            .range([0, width - marginLeft]);


        // Define X axis
        var xAxis = d3.axisBottom()
            .scale(xScale)
            .ticks(xAxis_max); // Set rough # of ticks
        // .tickFormat(formatAsPercentage);

        // Add chart
        var chart = svgElement.append("g")
            .attr("class", "chart " + auId)
            .attr("visibility", visibility)
            .attr("transform", "translate(" + marginLeft + "," + (marginTop + (barPadding / 2)) + ")");

        // Add chart titles to plot 1 and 2
        if (svgElement.attr("class") == pl2Svg_class) {
            chart.selectAll("text")
                .data(plotData)
                .enter()
                .append("text")
                .attr("x", marginLeft + (width - marginLeft) / 2)
                .attr("y", -fontSize * 0.5)
                .attr("text-anchor", "middle")
                .attr("font-size", fontSize * 1.2)
                .attr("font-weight", "bold")
                .text(function(d) {
                    return swapNamePositions(d) + "'s publications";
                });
        }

        // Add bar groups (bars + texts)
        var bar = chart.selectAll("g")
            .data(plotData)
            .enter()
            .append("g")
            .attr("class", "bar")
            .attr("transform", function(d, i) {
                return "translate(" + marginLeft + "," + (i * (barHeight + barPadding)) + ")";
            })
            .attr("id", function(d, i) {
                return plotData[i].barId;
            });

        // Add bars
        bar.append("rect")
            .attr("class", "rect")
            .attr("width", function(d) {
                return (d.x / xAxis_max) * (width - marginLeft);
            })
            .attr("height", barHeight)
            .attr("fill", barColour_unclicked);

        // Add text (number of publications)
        bar.append("text")
            .attr("x", function(d) {
                return (d.x / xAxis_max) * (width - marginLeft) - fontSize;
            })
            .attr("y", function(d, i) {
                return (barHeight) / 2 + fontSize * (1 / 3);
            })
            .attr("class", "pubNum")
            .attr("font-family", "sans-serif")
            .attr("font-size", fontSize)
            .attr("font-weight", "bold")
            .attr("fill", "black")
            .attr("text-anchor", "end")
            .text(function(d) {
                return d.x;
            });

        // Add text (y axis)
        bar.append("text")
            .text(function(d) {
                return d.y;
            })
            .attr("x", function(d) {
                return -fontSize / 2;
            })
            .attr("y", function(d, i) {
                return (barHeight) / 2 + fontSize * (1 / 3);
            })
            .attr("font-family", "sans-serif")
            .attr("font-size", fontSize + "px")
            .attr("font-weight", "bold")
            .attr("fill", "black")
            .attr("text-anchor", "end");

        // Create X axis
        chart.append("g")
            .attr("class", xAxisClass)
            .attr("transform", "translate(" + marginLeft + "," + ((barHeight + barPadding) * dataCount + fontSize) + ")")
            .call(xAxis)
            .append("text")
            .attr("x", (width - marginLeft) / 2)
            .attr("text-anchor", "middle")
            .attr("font-size", fontSize)
            .attr("font-weight", "bold")
            .text("Number of publications per " + svgElement.attr("class"));

        // Create dialogs for bar-click
        dialogsForPlots(svgClass, plotData);

        // interact with bars and text within them
        var oldBarId;
        var barId;

        $(".rect, .pubNum")
            // ".event(function()" results in jQuery firing multiple times
            // To avoid this, ".off('mouseover').on('mouseover', function ()" is used.
            // (code from https://stackoverflow.com/a/20881348/7194743)

            .off('mouseover').on('mouseover', function() {
                // change rect colour (mouse over bar)
                if ($(this).prop("tagName") == "rect") { // http://stackoverflow.com/a/5347371
                    $(this).attr("fill", barColour_clicked);
                }
                // change rect colour (mouse over text in rect)
                else {
                    // code from http://stackoverflow.com/a/2679026
                    $(this).closest(':has(rect)').find('rect').attr("fill", barColour_clicked);
                }
            })

            .off('mouseleave').on('mouseleave', function() {
                
                var changeColour = true;
                
                // For plot 1, do not change rect colour on mouseleave if bar has been clicked ("barId" is set on click).
                if ($(this).closest('svg').attr("class") == pl1Svg_class) {
                    if ($(this).closest('.bar').attr("id") == barId) {
                        changeColour = false; // See "Note 4" at the bottom. This line and the codes in mouseover does the same thing, but the approach is different.
                    }
                }

                // Change colour on mouse leave always for plots 2 and 3, and in all other cases for plot 1.
                if (changeColour) {
                    $(this).closest('.bar').find('rect').attr("fill", barColour_unclicked);
                }
            })


                // if ($(this).closest('.bar').attr("id") != barId) {
                //     // recover rect colour (mouse over bar)
                //     if ($(this).prop("tagName") == "rect") {
                //             $(this).attr("fill", barColour_unclicked);
                //     }
                //     // recover rect colour (mouse over text in rect)
                //     else {
                //             $(this).closest('rect').attr("fill", barColour_unclicked);
                //         }
                //     }
                // })

            .off('click').on('click', function() {

                // // change rect colour (mouse over bar)
                // if ($(this).prop("tagName") == "rect") { // http://stackoverflow.com/a/5347371
                //     $(this).attr("fill", barColour_clicked);
                // }
                // // change rect colour (mouse over text in rect)
                // else {
                //     // code from http://stackoverflow.com/a/2679026
                //     $(this).closest(':has(rect)').find('rect').attr("fill", barColour_clicked);
                // }

                // get bar group ID (author) of clicked bar
                barId_temp = $(this).closest('.bar').attr("id");
                // var chartClass_part = ($(this).closest('.chart').attr("class").split(" ")[1]);

                // react to click in plots 2 and 3
                if ($(this).closest('svg').attr("class") != pl1Svg_class) {
                    $('#' + barId_temp + "_dialog").dialog("open");
                    return false;
                }
                // react to click in plot 1
                else {
                    barId = barId_temp; // See Note 8 at the bottom regarding why "var" should not be used here

                    // do nothing if same bar was clicked before
                    if (oldBarId == barId) {}

                    // if different bar is clicked
                    else {
                        
                        /* display plots 2 and 3 */
                        // hide previously displayed plot
                        $('.' + oldBarId).attr("visibility", "hidden");

                        // display plots 2 and 3 of corresponding author
                        $('.' + barId).attr("visibility", "visible");

                        /* recover rect colour of previously coloured rect */
                        $('#' + oldBarId).find('rect').attr("fill", barColour_unclicked);
                        // //  when bar clicked
                        // if ($(this).prop("tagName") == "rect") { // http://stackoverflow.com/a/5347371
                        //     $('#' + oldBarId).attr("fill", barColour_clicked);
                        // }
                        // // when text in rect clicked
                        // else {
                        //     // code from http://stackoverflow.com/a/2679026
                        //     $(this).closest(':has(rect)').find('rect').attr("fill", barColour_clicked);
                        // }

                        // recover rect colour of prevoiusly clicked bar
                        // $('#' + oldBarId).attr("fill",.off('click').on('click', 600e6");


                        /* mouseover for plot2's line graph */
                        // Advice from https://stackoverflow.com/a/20837758
                        // See note 7 at the bottom regarding mouse events on overlapping elements
                        
                        // disable mouse events of previously displayed plot
                        $('#overlay_' + oldBarId).attr("pointer-events", "none");

                        // enable mouse events of currently displayed plot
                        $('#overlay_' + barId).attr("pointer-events", "all");


                        oldBarId = barId;
                        
                    }
                }
            })
    }

    function drawLineChart(svgClass, svgElement, plotData, auId = null, chartDim, visibility, xAxisClass, term) {
        // this function is based on codes at http://bit.ly/2qNRPbF

        var width = chartDim.width;
        var height = chartDim.height;
        // var barHeight = chartDim.barHeight;
        var barPadding = chartDim.barPadding;
        var marginTop = chartDim.marginTop;
        var marginLeft = chartDim.marginLeft;
        var fontSize = chartDim.fontSize;
        var dataCount = chartDim.dataCount;
        var dataValuesCount = chartDim.dataValuesCount;

        var dataValueMin = d3.min(plotData, function(d) { return d.y; });
        var dataValueMax = d3.max(plotData, function(d) { return d.y; });

        // quit if no data
        if (dataCount == 0) {
            return;
        }


        // parse and format the year
        var parseYear = d3.timeParse("%Y");

        plotData.forEach(function(d) {
            d.x = parseYear(d.x);
        });

        // determine number of ticks on x (number of years) and y-axes (number of publications)
        var xTicks = dataCount;

        var yTickMin = Math.floor(dataValueMin / 10) * 10;        
        var yTickMax;

        if (dataValueMax <= 5) {
            yTickMax = dataValueMax;
        }
        // else if (dataValueMax <= 10) {
        //     yTickMax = Math.ceil(dataValueMax / 10) * 10;
        // }
        else if (dataValueMax <= 100) {
            yTickMax = Math.ceil(dataValueMax / 10) * 10
        }
        else if (dataValueMax <= 500) {
            yTickMax = Math.ceil(dataValueMax / 50) * 50
        }
        else if (dataValueMax <= 1000) {
            yTickMax = Math.ceil(dataValueMax / 100) * 100
        }
        else if (dataValueMax <= 5000) {
            yTickMax = Math.ceil(dataValueMax / 500) * 500
        }
        else if (dataValueMax <= 10000) {
            yTickMax = Math.ceil(dataValueMax / 1000) * 1000
        }
        else if (dataValueMax <= 50000) {
            yTickMax = Math.ceil(dataValueMax / 5000) * 5000
        }


        yTickRange = yTickMax - yTickMin;

        var yTicks;
        if (yTickRange <= 5) {
            yTicks = yTickRange;
        }
        else if (yTickRange <= 10) {
            yTicks = yTickRange / 5 + 1;
        }
        else if (yTickRange <= 50) {
            yTicks = yTickRange / 10 + 1;
        }
        else if (yTickRange <= 100) {
            yTicks = yTickRange / 50 + 1;
        }
        else if (yTickRange <= 500) {
            yTicks = yTickRange / 100 + 1;
        }
        else if (yTickRange <= 1000) {
            yTicks = yTickRange / 500 + 1;
        }
        else if (yTickRange <= 5000) {
            yTicks = yTickRange / 1000 + 1;
        }
        else if (yTickRange <= 10000) {
            yTicks = yTickRange / 5000 + 1;
        }
        else if (yTickRange <= 50000) {
            yTicks = yTickRange / 10000 + 1;
        }

        // var yTicks = (dataValuesCount >= 2) ? dataValuesCount - 1: dataValuesCount;

        // scales
        var xScale = d3.scaleTime()
                    .domain(d3.extent(plotData, function(d) {
                        return d.x;
                    }))
                    .range([0, width - marginLeft]);

        var yScale = d3.scaleLinear()
                    .domain([yTickMin, yTickMax])
                    .range([height, 0]);

        // define axes
        xAxis = d3.axisBottom(xScale)
                .ticks(xTicks)
                .tickFormat(d3.timeFormat("%Y"));
        yAxis = d3.axisLeft(yScale)
                .ticks(yTicks)
                .tickFormat(d3.format("d"));

        // define grid lines
        function make_x_gridlines() {       
            return d3.axisBottom(x)
                .ticks(xTicks)
        }

        function make_y_gridlines() {       
            return d3.axisLeft(y)
                .ticks(yTicks)
        }



        // define the line
        var valueline = d3.line()
            .x(function(d) {
                return xScale(d.x);
            })
            .y(function(d) {
                return yScale(d.y);
            });

        // // append the svg obgect to the body of the page
        // // appends a 'group' element to 'svg'
        // // moves the 'group' element to the top left margin




        // var svg = d3.select("body").append("svg")
        //     .attr("width", width + marginLeft + marginRight)
        //     .attr("height", height + margin.top + margin.bottom)
        //     .append("g")
        //     .attr("transform",
        //         "translate(" + marginLeft + "," + margin.top + ")");

        // add chart
        var chart = svgElement.append("g")
            .attr("class", "chart " + auId)
            .attr("visibility", visibility)
            .attr("transform", "translate(" + (marginLeft * 2) + "," + marginTop + ")");

        // // Scale the range of the data
        // xScale.domain(d3.extent(plotData, function(d) {
        //     return d.x;
        // }));


        // xScale.ticks(d3.timeYear.every(function(d) {
        //     return 1;
        // }));

        // yScale.domain([0, d3.max(plotData, function(d) {
        //     return d.y;
        // })]);

        // Add chart title
        chart.selectAll("text")
            .data(plotData)
            .enter()
            .append("text")
            .attr("x", (width - marginLeft) / 2)
            .attr("y", -fontSize)
            .attr("text-anchor", "middle")
            .attr("font-size", fontSize * 1.2)
            .attr("font-weight", "bold")
            .text(function(d) {
                var lastName = d.au.split(", ")[0];
                var firstName = d.au.split(", ")[1];
                // console.log(d.ref);
                return firstName + " " + lastName + "'s publications";
            });

        // add the X gridlines (code from http://bit.ly/2sm1iZr)
        chart.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(xScale)
                .ticks(xTicks)
                .tickSize(-height)
                .tickFormat("")
            );

        // add the Y gridlines (code from http://bit.ly/2sm1iZr)
        chart.append("g")
            .attr("class", "grid")
            .call(d3.axisLeft(yScale)
                .ticks(yTicks)
                .tickSize(-width + marginLeft)
                .tickFormat("")
            );

        // Add the valueline path (line).
        chart.append("path")
            .data([plotData])
            .attr("class", "line")
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            // .attr("stroke-width", "2px")
            .attr("d", valueline);


        // Add the X Axis
        chart.append("g")
            .attr("class", xAxisClass)
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
            .append("text")
            .attr("x", (width - marginLeft) / 2)
            .attr("y", parseInt($(".lineChartAxis .tick line").attr("y2")) + parseInt($(".lineChartAxis .tick text").attr("y")) + (barPadding / 2 + fontSize)) // first two are tick size and tick font size
            .attr("text-anchor", "middle")
            .attr("font-size", fontSize)
            .attr("font-weight", "bold")
            .text("Number of publications per " + svgElement.attr("class"));

            // // pull the transform data out of the tick
            // var transform = d3.transform(tick.attr("transform")).translate;

            // // passed in "data" is the value of the tick, transform[0] holds the X value


        // Add the Y Axis
        chart.append("g")
            .attr("class", xAxisClass)
            .call(yAxis);


        // add scatter plot (circles) (code from http://bit.ly/2sNr0IA)
        var r = 4;
        chart.selectAll("dot")
            .data(plotData)
            .enter()
            .append("circle")
            .attr("r", r)
            .attr("fill", "steelblue")
            .attr("cx", function(d) { return xScale(d.x); })
            .attr("cy", function(d) { return yScale(d.y); })
            // .on("mouseover", function(d) { return d.y; })

        /* this has been discarded due to the chart looking messy.
        // display values above circles
        values = chart.append("g")

        values.selectAll("text")
            .data(plotData)
            .enter()
            .append("text")
            .attr("x", function(d) {
                return xScale(d.x);
            })
            .attr("y", function(d) {
                return yScale(d.y) - r * 1.5;
            })
            .attr("text-anchor", "middle")
            .attr("font-size", fontSize * 0.8)
            .attr("font-weight", "bold")
            .attr("fill", "red")
            .text(function(d) {
                return d.y;
            });
        */    
        
        // Create dialogs for circle-click
        dialogsForPlots(svgClass, plotData)        
        
        // show circle and X value on mouseover (code from http://bit.ly/2sh4J7E)
        var focus = chart.append("g")
          .attr("class", "focus " + auId)
          .attr("display", "none");

        focus.append("circle")
          .attr("r", 5)
          .attr("fill", "red");

        focus.append("text")
          .attr("fill", "red")
          .attr("font-weight", "bold")
          .attr("text-anchor", "middle")
          .attr("x", 0)
          .attr("dy", "-0.5em");

        // See note 7 at the bottom regarding mouse events on overlapping elements
        var overlay = chart.append("g");

        overlay.append("rect")
            .attr("id", "overlay_" + auId)
            .attr("width", width - marginLeft)
            .attr("height", height)
            .attr("fill", "none")
            .attr("pointer-events", "none")
            .on("mouseover", function() { focus.attr("display", null); })
            .on("mouseout", function() { focus.attr("display", "none"); })
            .on("mousemove", mouseMove)
            .on("click", mouseClick);

        function mouseMove() {
            var bisectYear = d3.bisector(function(d) { return d.x; }).left;
            
            var x0 = xScale.invert(d3.mouse(this)[0]),
                i = bisectYear(plotData, x0, 1),
                d0 = plotData[i - 1],
                d1 = plotData[i],
                d = x0 - d0.x > d1.x - x0 ? d1 : d0;
                // console.log($(this).prop("tagName"));
                // console.log($(this).closest(':has(.focus)').find('.focus').attr("class"));
            focus.attr("transform", "translate(" + xScale(d.x) + "," + yScale(d.y) + ")");
            // console.log(d);
            focus.select("text").text(d.y);
            // $(this).parent().find('.focus').attr("display")
        }

        function mouseClick() {
            var bisectYear = d3.bisector(function(d) { return d.x; }).left;
            
            var x0 = xScale.invert(d3.mouse(this)[0]),
                i = bisectYear(plotData, x0, 1),
                d0 = plotData[i - 1],
                d1 = plotData[i],
                d = x0 - d0.x > d1.x - x0 ? d1 : d0;
                // console.log($(this).prop("tagName"));
                // console.log($(this).closest(':has(.focus)').find('.focus').attr("class"));
            // focus.attr("transform", "translate(" + xScale(d.x) + "," + yScale(d.y) + ")");
            $('#' + d.barId + "_dialog").dialog("open");
            // focus.select("text").text(d.y);
            // $(this).parent().find('.focus').attr("display")
        }



































        // scales
        /*    var yScale = d3.scaleLinear()
                .domain([0, plotData.length])
                .range([sideP, width - sideP]);*/

        // var xScale = d3.scaleLinear()
        //     .domain([0, xAxis_max])
        //     .range([0, width - marginLeft]);


        // // Define X axis
        // var xAxis = d3.axisBottom()
        //     .scale(xScale)
        //     .ticks(xAxis_max); // Set rough # of ticks
        // .tickFormat(formatAsPercentage);

        // Add chart
        // var chart = svgElement.append("g")
        //     .attr("class", "chart " + auId)
        //     .attr("visibility", visibility)
        //     .attr("transform", "translate(" + marginLeft + "," + (marginTop + (barPadding / 2)) + ")");

        // Add bar groups (bars + texts)
        // var bar = chart.selectAll("g")
        //     .data(plotData)
        //     .enter()
        //     .append("g")
        //     .attr("class", "bar")
        //     .attr("transform", function(d, i) {
        //         return "translate(" + marginLeft + "," + (i * (barHeight + barPadding)) + ")";
        //     })
        //     .attr("id", function(d, i) {
        //         if (barId) {
        //             return auIdList[i];
        //         }
        //     });

        // // Add bars
        // bar.append("rect")
        //     // .attr("class", "rect")
        //     .attr("width", function(d) {
        //         return (d.x / xAxis_max) * (width - marginLeft);
        //     })
        //     .attr("height", barHeight)
        //     .attr("fill", barColour_unclicked);

        // // Add text (number of publications)
        // bar.append("text")
        //     .attr("x", function(d) {
        //         return (d.x / xAxis_max) * (width - marginLeft) - fontSize;
        //     })
        //     .attr("y", function(d, i) {
        //         return (barHeight) / 2 + fontSize * (1 / 3);
        //     })
        //     .attr("class", "pubNum")
        //     .attr("font-family", "sans-serif")
        //     .attr("font-size", fontSize)
        //     .attr("font-weight", "bold")
        //     .attr("fill", "black")
        //     .attr("text-anchor", "middle")
        //     .text(function(d) {
        //         return d.x;
        //     });

        // // Add text (y axis)
        // bar.append("text")
        //     .text(function(d) {
        //         return d.y;
        //     })
        //     .attr("x", function(d) {
        //         return -fontSize / 2;
        //     })
        //     .attr("y", function(d, i) {
        //         return (barHeight) / 2 + fontSize * (1 / 3);
        //     })
        //     .attr("font-family", "sans-serif")
        //     .attr("font-size", fontSize + "px")
        //     .attr("font-weight", "bold")
        //     .attr("fill", "black")
        //     .attr("text-anchor", "end");

        // // Create X axis
        // chart.append("g")
        //     .attr("class", "axis")
        //     .call(xAxis)
        //     .attr("transform", "translate(" + marginLeft + "," + ((barHeight + barPadding) * dataCount + fontSize) + ")")
        //     .append("text")
        //     .attr("x", (width - marginLeft) / 2)
        //     .attr("text-anchor", "middle")
        //     .attr("font-size", fontSize)
        //     .attr("font-weight", "bold")
        //     .text("Number of publications");



        // // interact with bars and text within them
        // var oldBarId;
        // var barId;

        // $("rect, .pubNum")
        //     .mouseover(function() {
        //         // bar
        //         if ($(this).prop("tagName") == "rect") { // http://stackoverflow.com/a/5347371
        //             $(this).attr("fill", barColour_clicked);
        //         }
        //         // text in rect
        //         else {
        //             $(this).closest('rect').attr("fill", barColour_clicked);
        //             // alternative code (http://stackoverflow.com/a/2679026):
        //             // $(this).closest(':has(rect)').find('rect').attr("fill", barColour_clicked);
        //         }
        //     })

        // .mouseleave(function() {
        //     if ($(this).prop("tagName") == "rect") {
        //         $(this).attr("fill", barColour_unclicked);
        //     } else {
        //         $(this).closest('rect').attr("fill", barColour_unclicked);
        //     }
        // })

        // .click(function() {

        //     // get bar group ID (author) of clicked bar
        //     barId = $(this).closest('.bar').attr("id");

        //     // do nothing if same bar was clicked before
        //     if (oldBarId == barId) {}

        //     // if different bar is clicked
        //     else {
        //         // hide previously displayed plot
        //         $('.' + oldBarId).attr("visibility", "hidden");
        //         // display plots 2 and 3 of corresponding author
        //         $('.' + barId).attr("visibility", "visible");

        //         oldBarId = barId;
        //     }
        // })
    }
}

/*
    // Define Y axis
    var yAxis = d3.axisLeft()
        .scale(yScale)
        .ticks(3) // Set rough # of ticks
        // .tickFormat(formatAsPercentage);

    // Create Y axis
    svg1.append("g")
        .attr("class", "axis")
        .call(yAxis)
        .transition()
        .duration(500)
        .attr("transform", "translate(" + sideP + ", 0)");
*/
// data for plot 2 (journals and number of publications)





/*

Note 1
".done" have been omitted because output of "NSuggest_CreateData"
could not enter it. Either ".fail" or ".always" works, but I chose the latter
to guarantee the return of output.

The "NSuggest_CreateData" was used for the following reasons. The "callback=?"
in the URL means that JSONP is requested instead of JSON. The JSONP came in
the format shown below.

NSuggest_CreateData("SearchTerm", new Array("suggestion1", "suggestion2", ... "suggestionN"), 0);

As the JSONP is received, "NSuggest_CreateData" is considered as a function and run
automatically. Therefore, I defined it so that the suggestions are returned,
based on the function shown below extracted from Pubmed's JavaScript file
(4001808.js).

function NSuggest_CreateData(q,matches,count){
  var rg = new RegExp('^' + inputText + '(@.*)?$','i');
  return jQuery.grep(matches,function(e,i){
      return rg.exec(e);
      }).length > 0;
}



Note 2
A ".getJSON" request is made each time a letter is typed into the textbox.
As new letter is typed, it would be nice to cancel all previous requests to reduce the
amount of data transfer.

If jsonP is requested, cancellation is tricky (http://stackoverflow.com/a/9999813).
Unfortunately, this script requests jsonP, and cancellation feature has not been added.

If JSON is requested, cancellation can be done by ".abort()" method. Below is the function "suggest"
with the cancellation feature added.

function suggest(query, syncResults, asyncResults) {
    // get places matching query (asynchronously)
    var parameters = {
        q: query
    };


    // Cancel previous request after new request is made (http://stackoverflow.com/a/12713532)
    if (typeof request !== "undefined") {2
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

            // call typeahead's callback with no results
            asyncResults([]);
        });
}



Note 3
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



Note 4
Both mouseover and mouseleave changes rect colour, but in different ways.
mouseleave's codes are simpler, but it always goes to parent element and comes back down to rect.
mouseover stays on rect if rect is clicked. Otherwise, it uses the same approach as the mouseleave's code.

mouseover:
The codes in mouseover first identifies what is clicked (i.e. rect or the text in rect).
If rect is clicked, colour is changed directly (from "$(this)")
If the text in rect is clicked, the closest parent element that contains the rect is found, then rect is found, and the rect's colour is changed.

mouseleave:
The closest "bar" class is found (which is the closest parent element that contains the rect), then rect is found, and the rect's colour is changed.




Note 5
Following code does the same thing. Does it do it differently?
$.when(removeGif(pl1Svg_div)).then(drawGraphs(data, suggestion.term));


Note 6
Perhaps this was an issue called "callback hell"?

__________________________________
-- Below is the current version. --

// load GIF image to display after submitting keyword
var loadingGif = new Image();
loadingGif.alt = "loading";
loadingGif.src = "/static/loading.gif";


displayGif(images_div, loadingGif); // See Note 6 at the bottom.
records(suggestion);
__________________________________

-- Following is the previous version
function displayGif(images_div, gif) {
    $("." + divClass1).css("justify-content", "center");
    $("." + divClass1).css("display", "flex");
    $("." + divClass1).append("<img alt='loading' src='" + gif + "'/>");
}

displayGif(images_div, "/static/loading.gif"); // See Note 6 at the bottom.
records(suggestion);
__________________________________

Such change has been made because the "getJSON" request in "records" was queued *before* GIF fetching in "displayGif".
This resulted in failure to display the GIF until plots were displayed after getJSON completion.

Although this problem diminished when the GIF was included as part of the "index.html", it still happened occasionally.

To compeltely prevent this problem, the GIF has been loaded as a variable before running "displayGif".

Another image variable, "apology", for "apologise" function has been prepapred for a different purpose





Note 7

When mouse events are set on overlapping elements, only the element on top responds to mouse events
unless the following two are done.

1. set the element's "pointer-events" property to "none". Below is code used in this script.

.click(function() {
        
        // disable mouse events of previously displayed plot
        $('#overlay_' + oldBarId).attr("pointer-events", "none");

        // enable mouse events of previously displayed plot
        $('#overlay_' + barId).attr("pointer-events", "all");

2. Create the element inside a "g" element.

________________________
This works (which is the current code)

overlay = chart.append("g")
overlay.append("rect")
________________________
The following doesn't work.

chart.append("rect")
________________________




Note 8

Using "var barId" here prevents plot 1's clicked bar from retaining its colour at mouseleave event.

This seems to be because using "var" limits the scope of barId within where it was created.

barId was initially created with "var" within "drawBarChart" function. This way, barId seems to make barId alive anywhere inside "drawBarChart" function,
making barId usable in all mouse events blocks (mouseover, mouseleave, click).

However, using "var barId" again in one mouse event block, barId seems to survive only within the block. So, if "var barId" is used again in the mouse "click" block,
any value saved in barId seems unable to be used in other mouse events. Mouseleave event depends on the value of barId, so this can cause problems, such as that
described at the beginning of this note.

Relevant info is at https://stackoverflow.com/a/1470494
*/



/*
Code below fetches info for 5000 articles. This took >40 seconds. The same task takes >30 seconds on Python (fetching takes around 1 second, and decoding the feed takes >30 seconds).

    id = {id: "28050894,28412661,28274168,27207190,28196717,28189716,27940258,27939248,27876552,27592563,27423491,27266391,28433741,28392471,28387438,27905179,28342226,28314070,28499565,26592488,28438540,28217976,28105670,28202261,28288869,28399440,28391027,28411046,27346369,27866508,27573679,27426892,27056022,27019391,27018550,28032255,27796500,27785605,27752826,27381016,27194554,27917685,28345275,28111056,28504043,28446041,28446040,28367717,28343053,28092781,28193583,28160626,28415414,28415407,28214997,28265686,28319837,28230072,28128334,28102228,27876425,28477647,28112057,27435825,27321864,28286284,28279926,28371658,28371656,28340425,28315577,28235589,28235586,28202410,28434616,28434615,28063469,27455897,28504928,28468528,28505127,28335009,28503978,28502262,28504703,28302570,28274820,28242439,28505669,28502243,28502099,28505103,28323012,28500770,28497655,28494655,28443355,28500472,28497707,28497892,28498274,28498796,28493592,28493561,28490020,28497215,28492091,28497380,28494198,28496171,28500871,28489950,28416594,28387222,28501553,28389239,28488770,28486227,28487307,28488252,28485998,28485405,28485403,28499504,28486094,28499901,28499897,28505469,28485257,28499767,28499766,28485732,28485731,28485725,28375719,28478771,28443349,28480992,28481370,28481666,28480579,28483739,28485076,28381728,28484822,28495493,28495492,28495491,28495490,28477384,28477407,28487157,28487076,28472900,28476141,28483271,28475123,28475373,28477285,28475360,28474363,28477070,28475861,28470106,28470099,28479143,28474173,28472198,28472557,28470468,28468693,28470477,28463847,28479324,28472294,28467611,28468999,28411272,28467540,28467520,28481349,28479102,28472659,28472655,28472649,28467426,28466366,28464976,28464965,28464963,28478887,28464848,28464243,28464773,28464830,28466270,28461698,28482197,28476336,28476335,28463241,28463237,27987262,27364459,28369804,28332705,26833821,27853950,28382557,28216175,28215901,28457164,28457153,28320223,28463346,28463343,28415138,27785856,28431029,28242149,28185228,28415873,28415871,28374606,27733710,28460529,28385625,28465387,28003154,28003152,27871802,28479528,28162976,28057452,27568378,27226446,28281277,27810903,28315614,27722855,28397113,28346041,28288547,28288532,28130726,28342379,28277876,28098496,28333692,28306564,28230632,28230631,28230630,28212174,28212171,28466069,28410959,28400155,28318898,28274506,28364686,28314165,28212505,28192769,28192768,28302653,28294453,28211093,28327916,28230289,28294459,28334860,28252452,28181959,28067751,28122258,27121916,28034960,28466749,28466747,28466745,28466742,28162014,28084154,28173881,28358526,28277733,28433088,28433087,28185044,28398819,28215710,28378559,28462458,27921323,28406840,28141633,28141631,28084537,27805291,28342832,28186671,27898171,27859486,27735078,27735056,27376697,27886806,28103519,28088727,28086126,28063323,28459416,28234206,27689884,28372526,28460148,28329400,28433073,28344044,28330589,27824682,27989882,27023224,28348382,28387341,27491537,28434949,28341151,28323201,27981679,27894892,27288319,28457189,28263800,28150964,28079061,27986973,27917869,27748741,28413940,28413935,28440047,28211248,28192131,27519538,27216638,28438236,28493247,28457205,28093055,28045349,28294477,28182301,28004481,27873453,27804186,28282630,28237912,28237910,28219026,28214778,28208077,28199911,28199909,28199908,28192770,28189940,28189075,28187335,28091349,28091343,28077184,28265714,28083675,27995279,28419390,28398574,28338967,28338845,28003467,27562855,27559077,27555659,27550776,27539951,27521348,27481827,27481826,27440672,27352782,27338279,27262112,27169464,28291690,28277308,27956009,27955800,27916288,27913159,27894822,27889384,27887780,27887779,27884433,27881233,27876273,27866695,27863935,27856157,27856156,27847228,27847227,27839914,27838097,27838096,28260128,28292639,28332369,28467893,28208070,28336432,28463798,28461223,28468274,28503156,28420824,28449636,28455369,28453389,28461252,28476012,28461117,28449613,28490709,28460810,28449643,28452148,28451897,28449199,28452080,28434268,28490882,28447622,28477547,28463718,28490910,28477447,28474052,28457774,28446482,28444578,28447217,28456376,28348135,28446243,28454982,28441663,28443616,28477548,28443534,28443529,28443526,28441976,28449132,28418645,28444556,28441335,28454059,28445633,28439101,28404897,28455126,28463714,28458083,28454923,28454920,28435979,28484422,28484390,28439787,28438837,28344127,28437438,28435992,28482196,28463748,28463717,28460282,28456026,28436345,28450056,28462815,28440197,28442424,28460284,28460280,28434159,28442422,28456024,28442250,28442249,28442247,28442246,28418641,28427286,28438555,28453184,28429622,28484400,28249940,28461752,28438466,28487497,28430790,28429844,28438437,28430839,28427114,28462881,28473777,28473776,28473782,28430670,28424430,28429076,28461748,28425497,28433652,28426817,28434719,28483022,28001356,28001043,28422271,28430672,28425060,28420451,28421867,28422422,28422133,28469558,28469556,28469581,28421658,28424076,28422371,28283562,28421871,28242730,28422427,28448805,28420450,28433501,28433500,28433499,28433498,28421682,28431689,28421333,28421639,28421313,28416810,28480163,28421529,28418011,28431901,28418288,28431800,28427930,28418402,28425244,28428814,28416966,28414583,28419586,28419772,28428048,28414766,28412897,28412895,28412889,28419491,28427929,28419656,28242499,28199893,28320191,28433949,28232170,28192273,28419874,28419824,28083901,28167336,28143767,28130172,28115219,28445800,28416445,28416295,28416205,28416094,28368577,28404984,28407747,28405888,28412921,28407198,28448820,28412910,28406327,28406662,28248104,28458550,28458549,28414078,28406917,28406913,28414084,28416095,28416092,28375612,28492956,28402033,28406538,28283561,28283559,28442912,28294132,28476014,28405711,28412089,28412088,28401916,28411148,28399850,28399842,28395527,28408348,28402427,28413439,28398117,28397632,28395674,28400569,28398293,28398343,28398342,28398340,28378993,28393745,28443016,28442992,28442991,28473889,28435276,28393474,28393897,28394697,28393621,28390407,28390399,28396239,28411576,28400070,28387925,28389889,28439515,28439248,28387726,28388259,28392482,28385166,28395940,28388932,28390877,28499489,28385707,28218498,28395192,28384101,28458998,28392266,28384650,28387484,28412612,28382874,28392209,28392208,28392207,28382934,28383650,28381420,28381222,28283557,28384469,28390892,28294137,28378644,28380075,28441618,28411573,28395229,28378204,28390851,28390850,28390849,28392828,28476208,28376877,28372555,28462882,28378228,28389049,28374220,28407554,28391108,28373685,28385492,28374661,28376926,28375211,28375210,28389130,28478998,28368091,28399428,28367774,28370942,28369688,28374238,28264565,28367711,28229913,28192174,28188811,28159590,28137432,28110862,28065843,28007463,28371955,28368138,28366115,28390296,28385587,28372995,27514629,27460766,27412497,27396868,28116993,28155220,28190295,28304149,28139055,27770494,28228056,28243833,28359438,28483104,28483101,28483097,28483096,28483094,28483093,28483084,28483080,28483079,28410561,28382844,28374601,28343435,28375060,27879426,28424797,27981425,28222891,28400969,28373235,28373226,28373219,27979819,28334978,27000096,26941174,28424401,27777273,27738261,27573257,27742926,27095825,28314460,27743205,28290080,28258365,28214752,28167327,28142098,28126482,28113098,28092774,27104779,26864713,28055336,28044455,28183735,28283211,25726949,25726849,25589153,28427946,27372353,27216590,28103961,28237833,27306965,27565806,27549216,27443319,26816222,27623819,28186680,28283227,28190661,28161246,28132567,28360375,28437056,28235557,28049009,27790829,28384043,27935798,28117515,28097738,28067006,28032370,28009080,28009070,26356360,27539022,28099880,28189549,28174109,27974056,28277736,28165261,28296627,28074354,28000013,27189697,27748550,27709604,28297593,28297590,28225749,28225745,28225521,28195931,28141623,28141622,28129314,27935442,28271422,28357975,28287057,28470156,28385096,27330059,28005578,28028641,28479803,28479802,28152499,28167638,28011441,27988332,27987480,28441905,28441884,28347261,28347260,28347257,28347256,28196430,28114835,27856682,27527735,27443599,28109841,28345513,28241183,28347436,28237639,28237638,28170299,28497736,28422845,27878417,28159330,28286248,28359144,28365874,26944284,26941103,26873854,27480494,27457809,27431292,28181877,28213064,27900577,28073591,28039001,28216171,28188887,28185872,28143762,27884698,28138895,28125326,27997274,27774843,27862704,26601913,26388498,28346060,28119185,28164355,28186496,27013076,27013075,28187106,28125460,27893590,27618173,27842472,27987251,28189922,28189096,28167435,28167432,28161615,28160655,28152400,28152399,28152397,28142068,28142065,28142064,28135643,28248562,28032535,27995817,27931266,27928975,27916012,27894376,27894373,27884217,28183030,28280881,28210783,28180960,26822967,28483177,28483174,28153646,28189442,28379529,28379483,28318837,28277310,28029516,27818077,27802910,27789188,27789187,27789186,27776953,27776952,27773385,27760701,27760700,27746053,27733301,27667369,27061476,28251244,28213300,28189910,28087837,28268034,28291295,28291293,28238293,27654063,27458023,28359200,28373127,28359301,28222314,28214564,28412616,28388455,28431278,28491312,28111261,28093254,28089851,28370163,28361258,28408985,28042091,28358316,28358303,28355928,28358131,28358551,28171781,28161644,28131010,28126618,28092779,28380108,28360420,28353136,28357563,28365388,28367307,28363835,28272498,28355219,28364963,28260370,28371232,28371072,28349649,28350371,28277864,28396652,28353125,28355041,28348384,28348381,28348379,28350822,28363766,28390294,28347393,28363347,28363346,28352126,28350401,28350400,28482249,28349247,28396623,28396641,28396640,28396643,28349344,28392697,28153689,28351548,28348393,28341872,28349512,28341945,28341942,28393090,28351597,28342141,28343349,28343167,28351544,28351543,28339164,28369257,28347521,28385386,28342013,28347569,28333365,28386219,28356723,28334045,28346773,28334488,28343741,28332626,28272861,28331058,28213444,28213441,28479973,28479972,28435648,28342897,28186095,28139679,28342945,28342943,28341443,28371682,28325167,28342578,28327583,28401047,28401044,28320224,28327107,28377698,28327175,28343067,28322279,28322275,28322273,28322246,28391138,28346888,28369646,28341002,28323286,28320371,28373848,28321286,28336496,28336493,28317220,28317218,28342330,28369639,28369611,28336195,28335457,28340122,28185672,28185671,28365536,28315932,28325573,28325572,28316115,28303578,28314932,28391102,28367128,28304340,28306157,28314733,28039324,28338977,28338954,28320578,28318835,28303968,28318911,28300292,28303373,28318841,28318840,28318839,28170220,28141924,27959513,28298276,28012850,28065900,28190425,27765268,27720199,27647218,27450031,27316853,27259817,28132910,28360829,28360866,28107668,28103521,28294711,27381164,27465045,27140693,26349010,28293778,28295391,28318836,28295046,28295013,28292279,28293803,28293729,28293286,28335437,28297592,28290733,28296070,28290151,28289284,28289282,28289280,28289279,28289277,27890827,27282085,27012612,28290743,28294468,28314681,28314680,28314679,28302395,28302394,28302393,28216146,28290073,28348512,28348532,28291058,28287773,28287187,28292624,28338943,28338919,28338897,28285452,28371744,28344592,28414930,28281921,28281552,28283886,28288855,28314621,28291692,28291691,28331332,28182195,28274209,28281097,28274298,28388490,28273009,28285148,28278537,28318609,28315621,28285734,28285029,28337131,28325680,28275903,28288440,28285028,28285026,28285025,28285024,28285022,28431868,28270120,28270387,28326054,28316773,28267713,28282638,28301828,28285246,28267149,28301776,28321200,28287964,28343762,28272307,28263090,28314129,28265857,28348953,28137649,28279571,28260235,28261797,28270338,28316580,28273823,28338900,28258047,28258445,28424542,28257447,28338892,28268041,28256527,28253016,28473946,28253899,28293111,28463820,28249639,28273278,28262436,28345848,28211669,27885490,28231044,27988937,27987221,28353293,28353290,26471731,28004866,27919183,27919182,27771971,27002542,28147467,27804260,27734592,28218055,28218054,27811138,27687777,27687775,27117756,27004487,27916686,27825934,27725171,28225304,28137374,28174121,28092449,28451387,28169167,28493605,28009436,28153927,28104737,28069563,28077398,27940260,27890662,27884623,27964871,27867023,27369464,27334340,27638424,27005988,26965907,26946125,26941382,27543496,28251450,27930934,28497008,28258419,28253092,28253091,28005458,28219788,27589556,28124262,28387211,27400927,27889833,28142106,28049083,28049080,28049076,28049075,26593886,28450949,28450912,27766914,28140680,28129701,28052701,28001435,28346630,28274335,28081869,28062232,27859903,27774734,28334933,28370311,28370310,28370309,28370308,28332719,27941358,27898432,27755155,27685179,28242031,27669573,28134026,28457093,28166439,27996343,28033521,28012350,28219485,27362838,26923489,28323458,27786353,28152454,28146614,27753758,27668942,27428480,27428476,28153058,28418833,28025777,27888397,26785056,28031399,28137973,27573722,28180026,28356628,28248434,28291036,27951451,27940386,27898324,27898323,27886638,28245176,28245175,28245174,28317509,28114601,28097367,28236956,28236950,28236949,26961817,28484349,28236841,28353559,28272261,27647538,26803493,26780454,27457813,27240532,27001617,28112735,28155901,28236096,28007586,27993645,27866902,27857125,27629369,27577602,28104410,27965136,27810425,26721665,28247817,28275106,28038867,27917593,26856250,28087443,28208190,27656915,28291976,28291975,28291971,28291970,28291969,27399592,28368184,28368183,28368182,28368180,28368179,28182471,27560455,27547856,27547852,27281040,28245706,27799019,28261925,28039921,27470981,28326122,28326117,28326114,28326111,28152470,28142103,28126575,28113122,28104564,28104562,28095336,28081455,28063395,28063393,27873559,27866482,27834153,27830632,26886575,28027496,28012291,28154892,28078393,28153339,28139249,27028661,28025717,28489133,28322591,28344488,28399309,28399308,28399307,28177077,28057720,28003469,28003468,27535082,27507268,27451428,27445261,27421793,27421792,27384054,27369471,27306316,27231308,27169465,28277309,28258794,28185783,28179064,28029515,27890401,27771201,27765522,27765521,27756514,27751654,27746054,27745755,27742161,27720315,27650194,27639418,27637363,27613511,27613509,27590573,28348731,28344764,28325111,27223864,28246140,28247157,28249166,28138118,28138115,28138113,28138109,28293174,28264500,28242871,28280344,28257849,28245266,28257853,28024236,28012424,28012423,28241891,28258835,28244984,28194935,28275713,28289391,28289394,28261479,28238272,28240266,28241019,28454051,28273629,28256300,28240740,28455901,28455894,28455891,28334138,28238173,28043915,28245961,28285208,28231716,28302261,28181956,28498090,28498089,28498088,28233913,28238731,28282533,28273630,28260643,28242107,28242106,28231610,28231777,28240189,28230315,28280463,28280477,28260904,28234442,28230171,28229240,28235555,28259035,28242515,28222824,28338779,28338769,28237606,28237605,28219455,28270751,28235554,28223265,28220043,28260899,28224285,28236519,28221369,28221368,28221366,28220613,28225439,28220356,27923740,28223162,28220654,28334240,28254200,28032990,28212630,28276863,28261117,28278613,28398817,28216334,28223031,28209179,28209774,28218788,28210873,28207753,28202095,28338738,28207073,28215471,28215470,28215391,28205609,28121123,28289436,27576130,27527822,27519822,28205038,28261115,27439997,28017919,27919751,27916665,27915121,27554533,28198022,28196460,28198409,28212793,28194004,28194003,28243099,28243097,28193301,28214176,28214174,28195573,28195572,28195569,28196512,28192643,28193197,28193195,28243212,28243211,28132591,28289475,28348956,28275544,28223096,28204755,28202291,28188687,28190094,28188958,28231496,28275545,28237759,28199713,28203265,28183293,28188388,28239362,28239361,28186690,28226264,28187187,28187217,28183367,28187219,28184875,28190639,28186152,28190690,28189758,28183281,28181901,28185094,28187054,28276964,28180904,28189532,28189530,28183340,28337332,28178977,28228718,28228737,28208695,28025253,28181189,28223808,28177184,28255444,28177507,28177089,28187965,28179504,28282734,28035805,28174827,28223929,28223982,28176008,28167837,28223812,28223811,28166863,28166848,28170004,28170002,28202296,28166757,28220103,28220059,28220083,28220082,28152356,28166306,27072377,26925706,28177063,28185786,28185785,28185784,27871923,27371348,28174128,28179063,28237133,28174035,28169087,28217082,28152600,28017662,28169089,28169088,28174595,28243459,28152990,28210217,28150512,28162810,28263522,28252893,27925164,27922183,27870529,27864826,28195778,27823940,28142274,28142272,28142267,27771972,27609240,27523502,27997229,27901521,28104068,28104067,28104060,27704220,28262180,28262177,28262175,28262174,28262173,28262171,28262165,28262162,28262155,28262150,28262149,28262147,28262146,28262129,28262127,28090790,27920065,27920064,27913580,27609940,27755061,28044359,28267988,27769567,28049619,27993517,28184317,28143492,27810893,28082298,28007987,27897031,26723567,28150086,28239791,27586960,28157454,27605579,27481921,27335156,27310245,27310243,26733534,28182345,28056388,27706797,27367612,27846438,27838461,27996211,27295054,26298476,28040575,27923116,27852471,27444616,26307497,27838588,27603523,26864886,27717222,28086176,27625143,26616380,26256570,25582878,25582595,25529847,28094235,27658991,27216589,26923995,26961343,26753632,27377417,26910404,26499939,26310877,28089652,28062203,27986355,27939135,27992837,27992836,27992834,27855309,27837669,27837667,28100506,28096176,28011708,28243163,27997809,28166363,28088314,27732116,28203201,27862351,27806441,28035465,28113193,27819519,28142061,28386521,28043031,27996189,27600259,27815515,27929689,27395390,27930915,27888723,28171735,27815320,28112539,26983067,26771226,26131914,27825609,27796029,28234436,28002662,28027114,28027110,27977467,27328754,26025842,27690706,26649857,26518213,27310606,28082513,27928859,27837658,27835738,28168926,27729563,28107885,28099769,28087201,28165438,28110691,28225484,27488109,28035416,28277568,28277567,28277565,28277564,27879341,27956746,27956744,28283114,27992416,27575297,27864083,27751941,27848117,27784625,27717880,27678413,28203084,28203081,28126626,28093278,27808537,27515791,27993603,27986468,27995564,27856235,27834101,27774832,27670756,27658459,28163559,27986516,27907838,27755991,27923717,28143732,28126054,27776093,28150091,28142382,27799016,27691375,27873471,27673731,27676126,28064092,28038438,28033512,28033511,28024180,28024179,28002758,27988426,27988425,27808013,27776571,27951520,28025742,28089383,27424873,28160835,27939828,27784534,27645107,27613507,27567291,27531067,27510855,27449252,27317361,27269670,26920092,28040825,28032136,28028581,28013327,27847980,28092756,27299747,28255435,27861318,28127934,28127931,28127922,28127915,28135847,28143464,28234211,28138157,28139642,28096412,28139772,28140405,28140401,28133766,28194095,28132660,28141630,27867012,27856274,28138965,27987389,27960147,28338753,28148460,28143678,28139359,28127888,28203078,28130870,28139360,28139358,28139357,28139356,28125984,28126703,28125634,28125578,28126896,28131599,28126031,28174594,28122703,28122697,28125008,28203529,28122016,28131598,28131597,28120939,28010158,28118821,28122240,28116777,28116752,28115742,28115738,28115737,28149692,28074037,28130005,28130004,28130003,28130002,28117840,28111843,28112487,28167919,28190035,28114315,28112079,28126360,28112043,28112029,28112021,28159336,28119036,28119035,28103712,28115272,28107388,28107346,28106314,28117104,28102528,28108498,28117000,28154566,28102512,28112711,28102331,28100191,28100262,28103775,28100238,28226265,28100276,28065648,27939355,28099526,28099444,28111064,28109669,28109668,28109667,28109666,28109665,28116741,28096070,28095817,28095813,28124599,28102978,28093569,27992373,28095495,28110814,28108228,28108227,28108226,28108225,28094815,28094814,28094812,28093868,27321914,27222040,28110815,27732892,27659554,27215477,27113501,27914948,27939174,27544423,26723568,26581337,28029428,27810272,27794254,27792967,27744125,27641441,27725313,27177764,27012503,26690803,26658930,28095309,28100419,28088223,28096781,28095998,28095997,28086761,28086792,28084841,28084500,28085950,28094171,28094170,28094169,28082379,28078741,28162778,28088913,28127276,28127290,28085108,28082257,28138247,28081145,28102975,28099629,28077156,28078547,28348631,28127577,28089135,28089134,28087270,28071963,28068943,28073796,28074346,27825865,28070123,27894920,27890741,28075410,28087269,28071747,28072415,28072414,28072411,28072661,28068398,28082140,28082139,28073465,28073606,28073605,27618739,28062471,28059046,28067944,28111561,28060877,28069313,28062923,28056892,28105006,28105021,28054432,28057610,28057607,28064060,28065484,28063940,28054990,27922594,27799474,27733502,27614213,27528110,27521758,28049472,28049441,28049620,28044064,28045645,28053019,28049760,28049759,28062262,28045139,28045464,28064233,27870441,27191837,27858959,28353255,28353250,28353249,28353248,28353246,28353244,28353243,28353242,28353232,28353231,28353227,28353225,28353222,28132184,27638627,28427558,28005316,27749984,27876351,27840055,27745822,27865048,27984264,27601046,27932669,27815720,27889374,28118726,28093927,27535956,27066817,26883570,26698819,28139947,28251031,27591184,27575949,27743041,28077222,27974147,27876157,27876155,27832841,27720388,27720198,27692238,27452791,27206569,26946382,26705848,28401151,28373983,28326328,28280741,28197415,28029458,26892851,28031224,27622678,27615793,27044051,28303200,26503264,28252307,27816667,28056537,27170669,27866120,24496045,28011898,27826741,28005457,27921860,27816847,27816846,27736667,27951456,27829340,27338741,27396304,26915421,28097634,26728170,26728167,26577915,27086781,27473368,28203040,27864791,27979975,27690184,27600596,27955831,27919523,27887859,27842941,27992809,27821355,27810612,27093552,28041576,27534376,27995392,28234658,27269896,27752767,28011714,28120489,28120487,28120486,28250496,28216785,28216783,28216782,28250567,28250565,28250552,28042663,27753686,27289503,28267822,28449629,28154279,28293047,28293046,28496495,27893230,27709980,28341015,27736738,27723546,27718456,28035928,27993232,27993229,28243470,27442352,28274083,28274026,27929612,27780336,28141710,28166471,27858591,27976820,28009525,27922908,27848034,27896809,27778340,27435966,27832597,27469358,27789681,28405133,28072646,27776293,27764693,27697587,27391101,27091719,27353026,28135389,27926742,27926741,27851843,27965002,27932233,27932232,27998332,28099358,28099356,28099349,27896755,28062709,26768595,27777417,27646261,27620842,27021823,26903271,28260775,27918536,27869829,27892953,27811930,26975653,28255461,28239498,28163934,27670235,27484578,27236079,27342123,27245499,26944732,27654215,27562377,27550734,27440007,27916709,27884751,27866942,27984197,27793700,27633835,27932026,27825840,27613888,27701952,27598719,27564411,27563937,27387772,27348781,28252572,28408971,27789118,27673421,26461045,27439544,26269122,27557994,27992301,26503818,27414740,27414739,27810494,27718271,27684946,27466037,27890810,28424383,28424378,27629797,27524369,27800670,28096883,28096881,28096877,28096876,28096874,28316973,27987484,27984822,27951481,27951479,27940324,27936437,27918972,27893996,27888683,27886580,27886578,27871032,27871031,27871030,27863321,27863314,27863313,27863311,27054620,27776572,27776560,27654902,27650432,27640523,27334937,27825069,28273660,28268224,28259879,28226318,28196359,28132055,28095382,28073112,28064283,27978520,27815602,27807604,27774567,27725997,27887740,27871760,28256360,28291864,28273271,28193373,28193369,27919467,27939025,27777062,27053545,28287196,28053131,28053130,28053129,28044008,27872267,27872266,27872259,27798225,27665001,27613806,27605526,27343007,27289116,27245172,27209638,27190279,27165690,27131155,25669851,28038918,27746052,27743650,27733302,27727006,27720316,27720314,27707530,27693281,27686279,27665257,27650196,27624681,27623360,27613506,28348889,28246557,28364465,28065291,28065287,28101323,28101321,28101319,28101318,28098923,28212953,28215308,28334543,28339416,28049887,28399104,28374703,28374702,28374699,28374697,28252601,28252597,27613293,28168960,28042822,28039552,27639091,27608809,28217181,28036406,27899214,27839827,27838019,27838018,27837680,27836244,27836243,27836239,27829509,27829189,27825786,27825784,27825780,27823797,27821363,27821360,27810229,27794276,27792977,27792975,27788460,27770713,27764741,27750116,27750115,27744232,27741482,27723522,27721059,27718468,27697656,27690134,27669496,27669495,27664549,27657804,27639816,27699909,28039421,28042814,28105267,28035472,28036092,28041919,28041917,28032254,28032202,28096678,28030616,28030584,28077240,28040324,28082874,28027370,27852062,27811378,28038921,28038920,28038919,28034792,28019715,28163856,28013441,28017130,28066248,28066271,28017817,28211553,28017493,27844503,28004385,28002957,28008071,28017494,28078209,28078207,28078203,27617634,28009624,28217272,28004339,28012640,27885918,27996318,27996317,27996316,28000544,27997288,27994220,28011131,27996024,27995975,28065233,27991722,28066272,28007464,27988852,27751959,28197318,27978770,28018476,28187857,27982537,27992436,27977285,27555534,28117049,27086544,27856084,27978811,27765579,27977851,27977041,27976370,27981413,27974084,28008260,28008259,27976606,27977720,27989645,27984131,27855565,27960654,28138403,28008301,27960624,27974613,27776076,27973619,27988073,27965312,27911814,27986430,27979699,27959332,27959331,27959329,27959328,27955666,27955645,27938391,27957657,27979698,27941946,27966426,27942861,28018213,28003749,27936112,27939555,27934937,28073491,27931201,27927259,28008319,27932499,27927736,27959478,27923415,27927242,27927173,27927957,27994466,27955801,27999553,27922606,27922604,27920282,27939829,27922632,27922130,28117656,27920085,27919211,28405585,27980408,27915397,27432008,27382048,27914041,27913877,27922589,28116236,27769892,27756686,27977091,26831447,28105289,27121754,27099073,27749256,28479897,27444940,27929269,27762073,27727512,27573569,27312590,27103199,27761925,28083609,27888978,27888977,27888976,27888974,27888956,27888954,27565803,27787965,27028544,27931920,27931919,27931918,27931917,27931915,27931914,27931903,27931902,27931901,27931900,27931893,25934162,27821411,27217425,27207861,27056176,27590078,27194777,27091289,27826006,27768984,27497442,27399803,27864917,27445354,27913408,26678596,26489977,27693417,26852023,26754839,26749003,26740229,26721794,27785696,27246199,27562725,27771557,28044942,27629292,27531181,27181114,27984260,27909826,27770667,28191386,27696144,27618303,27910804,28179808,27539712,27975362,25601015,25529756,25496290,28236992,27644914,26423605,26831320,27842943,27743760,27507227,28035183,27658674,27813431,27771981,27578530,27754856,27378802,27511297,27477775,27477494,27567986,27541329,27747539,28210523,27858347,27842249,27272342,27565762,27432534,27293176,27535345,27815512,27911137,24567364,27565651,26921166,27992258,27676420,27154343,28180029,28208982,27634495,27663579,28086018,28086013,28086010,27835719,27780332,27454547,27761777,27811555,27811553,27805978,27755220,27755219,27755159,27753728,27749681,27662459,27662458,27626286,27626285,27827293,27607568,27607567,27356089,27259074,27935733,27453210,27591787,27906088,27991418,27668353,27483114,27517838,27503083,27655963,27582295,28163499,28195063,27909173,27539930,28001283,28001282,27299643,27329321,27829096,27806157,27784035,27816569,27816567,27989735,27793698,27748930,26637325,27725656,27698434,27457814,27001614,26903267,26809838,27787935,28273770,28008202,27618311,27553839,27580848,27569994,27480797,27865707,27822729,27825906,27793657,27693668,28259864,28259863,28259862,28259861,27353310,27702600,27693229,27593442,27456824,27425770,28360811,28360809,28360807,28360801,27866493,27748565,27363988,27250524,27885961,27588387,27212191,27765659,27914511,27439988,27718340,27836161,27836150,28035126,27855437,27755292,27668412,27285059,26875104,26875101,26687510,26687383,27547854,27903175,27582242,27476806,27364816,27364810,27655012,27605034,27750143,27608362,27640177,27631410,27620899,27550459,27916287,27650195,27637362,27632907,27623361,27617415,27617414,27617413,27615408,27614570,27614569,27614568,27613510,27613508,27613505,27595554,27595553,27595551,27595550,27591821,27905557,27761599,27744541,27421906,28008348,27832914,27903282,28078183,27776390,27776389,27776386,27776383,27900651,27965600,27744190,27639163,27620326,27591412,27591410,27591408,27573056,27573055,27568303,27567194,27565700,27565699,27562225,27552670,27543831,27543828,27541345,27541344,27526318,27526316,27526312,27526311,27521746,27909250,27897969,27639363,27598234,27896805,27919404,28491826,27957319,27900676,27913162,27913161,27913160,27913157,27897266,27898074,27898073,27898072,27965562,27895084,27896651,27932884,27889922,28123834,27884145,27885664,27888379,27894237,27932973,27894821,27884042,27932945,27886132,27920539,27920538,27901213,27884931,27882449,27932948,27933003,27685665,27878761,27880854,27889385,27889382,27876866,27876020,28127520,27964941,27879657,28096775,27874011,27834215,27874048,27903342,27871263,27818178,27866510,27868463,27872269,27872268,27872261,27872260,27872257,27871302,27784192,27866272,27869767,27615033,27863524,27863522,27863252,27909421,27864402,27939053,27887704,27942450,27855222,27852112,27853241,27846922,27891188,27865768,27851771,27712136,27466625,26612516,27717652,27846841,27639297,27895608,27449547,27423424,27616476,27845416,27845781,27845777,27712130,27895602,27842596,27862846,27911416,27881919,27881918,27841092,27838738,27841067,27841057,27838828,27834490,27621318,27956832,27734750,27834905,27717827,27882189,27907273,27839913,27830729,27829443,27825323,27829454,27829400,27829392,27829384,27863039,27860369,27881965,27911756,27911749,27911743,27838441,27868083,27712141,27821210,27837583,27877101,27877130,27877142,27861956,27824163,27824119,27872683,27872587,27853387,27819315,27815839,27826070,27853371,27847593,27857698,27857696,27843322,27818357,27808414,27812142,27495358,27492675,27421706,27381554,27375133,27371157,27025976,27807413,27807157,27804008,27385617,28033691,27665849,27585549,27404582,27206671,26193335,27409573,27444795,27901520,27490838,27213890,27756771,27670833,27478139,27142119,27620269,27392942,27177811,28255578,27624522,27870507,27782355,27378314,27333588,27168196,26996274,27526115,27802977,27388573,26719216,27235930,27109609,27648976,27519536,27878726,27211362,27618632,27365164,27363344,26555700,27632064,27550371,27417321,27809671,27736366,27710199,27306990,26470695,27653782,27636509,27621208,27580313,27479694,27831757,26728764,27633376,27594595,27594444,27539538,27448295,27479649,27743547,27497990,27639442,27712862,27935810,27630220,27586196,27846655,27846652,27846651,27796257,27509263,27928189,27342447,27329212,27246897,27859668,27071182,27942062,28361822,28031586,28031582,27571460,27483421,27434314,27416102,27644152,27521534,27734716,27552677,27551753,27409157,27577961,27696929,27681707,27200500,27344622,27806863,27292410,26771824,27295077,28076667,27574838,28221900,27903327,27775257,27783555,27783548,27783545,25504547,27105456,27535377,27512021,27630144,27860079,27624838,27824784,27824776,27505440,27501141,27484635,27468165,27756833,27678088,27624147,27539931,27226342,27805715,27668670,27732705,27732692,27732689,27654151,27847437,27794367,27720402,27720401,27528095,27893665,26572640,27801890,27756909,27595595,26857598,26809842,26809841,26754951,27783068,27783067,27783065,27783064,27694994,27668389,27630045,27545441,27553784,27426839,27423256,25217064,27544826,27539962,27528587,27436721,27422408,27617637,27319970,27235082,27354230,27577742,27811454,27284637,27661005,28083028,27001122,27095082,27832676,27737475,27737473,27458742,27554461,27196141,27791105,27776604,27885309,27524364,27417897,27364809,27301767,27301766,27301765,27392126,27909459,27909454,26756206,27605254,27604840,27576609,27534999,27516217,27441416,27513883,27504985,27448523,27448522,27450659,27418108,27755933,27869872,27742234,27829813,27607184,27566843,27521349,27217271,27217270,27190280,27179125,27174556,27169466,27153864,27109925,27105903,27086079,27056717,27033329,27033328,26994395,26980144,26980142,25181987,27372255,27335180,27236410,27184458,27156647,27156240,27132494,27130562,27094720,26972474,26971072,26948503,26922657,26876311,26827128,26545296,27803977,27796403,27934603,27934596,27800031,27801899,27801894,27801893,27990037,28105280,28185594,27804883,27826194,27992889,27662482,27543916,27525830,27525829,27525826,27525824,27517342,27512922,27512917,27512914,27512913,27479105,27479104,27479101,27474857,27474856,27846049,27984074,27796754,27796922,28043646,27802911,27788673,27796745,27872811,27639959,27637389,27637386,27788640,27792727,27989726,27857778,27760116,27822050,27788194,27835733,28169816,27782878,27833555,27814962,27786182,27783677,27782768,27782767,27843348,27779093,27826551,27822046,27798224,27798223,27793422,27772538,27775408,27776504,27797817,27783051,27797829,27666479,27641663,27769213,27770284,27343851,27766621,27799749,27748333,27772665,27812321,27764107,27762319,27434874,27807403,27807401,27759181,27798135,27764671,27563737,27756899,27803662,27803654,27803648,27777633,27752082,27752079,27752140,27754483,27754480,27929229,27663068,27663065,27663064,27364036,27113498,27113497,27056754,26954565,26876947,26602589,26475673,26913808,27593571,26883068,27756689,27476436,27743219,27790159,27739330,27813505,27407109,27737831,27737649,27790089,27790607,27566723,27732817,27734887,27734956,27733145,27733539,27732740,27731949,27785123,27729083,27738648,27711412,27730479,27726284,27727180,27726054,27725659,27725655,27785036,27727317,27730532,27729486,27727244,27760654,27641766,27745717,27723806,27723782,27721451,27721389,27718890,27843445,27712119,27774073,27753759,27785454,27616482,27713834,27716115,27714552,27716508,27766084,27712400,27585752,27581525,27373850,27761108,27761127,27704675,27757142,27703225,27705802,27702810,27757090,27717830,27698361,27701407,27701405,27994742,27716110,27696361,27690670,27752241,27216283,27177972,26925705,27137767,27497263,27437875,27294331,27616350,27994714,27526990,27329688,27690548,27363508,27113123,27015370,27654247,27654241,27654236,27654229,27173485,27759808,27926378,27969086,27969085,27969076,27969070,27969067,27130725,27076497,26988230,27872693,27363923,27312268,27306571,27628506,27268516,27543973,27002704,26971470,27502027,27485658,27346367,28155422,27578772,27612279,27507786,27389944,26658937,27356920,27048911,26711096,27624435,27624431,27624428,27624426,27624421,27565775,27552661,27656786,27567529,27544689,27112918,27697135,27699943,27483346,27483345,27528493,26727888,27449495,27699643,26812939,26403538,25234230,27733313,27650867,27649638,27623121,27017316,26995151,27232296,27305925,27272500,27250978,26769121,26482736,26921232,26748100,27546373,27527256,27524298,27511320,27668551,27614143,27609312,27167520,27278672,27492617,27582038,26520152,27992057,27393575,27380241,27466199,28256473,28197009,28197005,28197002,28196997,27975000,27450504,27432262,27428251,27833522,27843467,28243293,28050187,28050184,27532874,27732031,27732025,27583768,27295376,26686292,27998264,27998263,27384868,27105181,27891433,27891431,27788312,27788310,27574835,27129094,27580497,27580496,27580495,27508430,27504593,27433851,27433850,27655250,27624166,27525637,27441460,27194229,27173384,27116682,26525923,27402173,27206718,27302861,27567591,27818011,27121900,27451107,27367209,27359327,27091718,27568504,26913382,27627029,27626788,27438791,27438689,27438537,27288068,27569526,27567466,27236774,26491028,26409480,27867941,27867940,27867938,26782053,26666204,26666201,27533299,27485950,27830164,27662527,27372546,27260325,27184339,27421225,26450593,26396150,27342132,27179799,27147081,27116999,27093226,27719778,27272046,27428765,27391358,27531135,27548835,27315048,27096222,26999687,26981879,27691394,27247177,27247173,27539233,27233969,27704581,27704577,27649341,27523641,27523506,27516123,27502153,27468631,27451917,27396386,27050714,27388688,27333159,27572830,27557949,27553822,27530989,27527585,27525990,27359171,27343471,27969002,27291830,27567733,27567290,27562615,27554199,27554198,27554197,27546092,27543252,27539074,27534680,27522263,27515987,27502427,27499362,27499361,27492755,27481817,27476650,27474348,27464451,27461400,27461399,27450778,27450777,27450776,27449251,27443808,27435059,27427558,27427557,27424267,27424266,27422333,27401532,27401531,27401530,27397721,27396837,27377977,27374322,27349816,27349815,27349814,27344986,27344363,27341953,27338758,27338757,27328889,27318522,27318521,27317360,27293136,27283452,27264503,27262384,27261419,27261418,27261417,27256518,27245710,27242068,27242067,27237600,27237599,27237598,27236409,27236408,27234344,27230289,27320736,27397570,27241797,27721972,27721970,27721969,28076642,28076640,27711938,27711937,27711935,27921424,27734702,26086792,25751661,27717278,27717277,27716175,27746712,27703436,27746755,27236031,27689860,27450747,27450744,27450743,27449010,27449008,27449007,27442977,27434201,27428085,27428084,27423634,27423123,27419653,27419650,27416540,27416538,27376670,27376666,27367492,27687783,27749965,27884423,27684654,27685352,27512062,27755520,27683010,27681572,27685194,27683516,27677625,27733830,27683283,27683901,27682896,27738647,27678536,27669819,27692350,27729865,27703840,27678498,27670918,27676446,27668891,27827340,27725796,27668757,27673467,27665002,27708677,27673502,27663585,27713690,27666382,27660274,27703363,27703362,27657540,27679779,27679778,27679770,27658371,27708591,27708604,27655387,27650396,27618677,27703357,27651212,27648956,27663045,27650395,27648571,27658989,27507698,27703333,27643618,27639558,27638491,27644915,27637201,27695408,27695423,27695425,27706734,27854086,27247142,27185738,27837920,27837918,27629871,27651829,27628485,27629273,27253217,27703560,27703552,27841934,27629158,27683568,27639448,27629985,27623690,27626659,27621217,27624616,27695333,27622935,27622934,27620627,27618789,27618693,27955939,27616045,27615810,27615800,27612527,27457803,27613560,27613435,27609030,27623123,27667973,27611660,27634797,27832840,27606629,27568681,27747152,27604177,27604363,27656120,27656159,27601421,27831672,27568567,27484634,27453061,27596719,27592556,27689019,27660490,27590010,27900342,27590844,27586404,27404479,27295520,27182769,26512011,26411564,27917216,26046823,27788777,27184105,27004590,26990377,26968334,26954460,27282362,27603450,27590304,27551024,27020720,26440145,26346037,26314952,27465649,27187203,26805584,28239676,27833939,27496211,27476142,27759212,27774781,27198162,26756621,25884235,27924116,26487590,26209938,27393467,27209172,27486153,27486148,26103941,27372312,27438900,27626066,26801682,27295491,27025904,27393806,27371790,26581838,27980891,27757063,25148542,27458700,27529801,27448238,27470221,26404636,26370275,26315603,26227799,27062554,27376639,27496573,27474687,27452144,27424800,27424799,27394076,27447101,27442981,27429167,27302677,27588066,27207070,27447338,27322602,27411376,27400736,27399875,27651012,27682868,27194114,27118810,27501209,27145016,26292345,27833241,27833234,27833230,27833222,27833221,27276401,27524273,27622655,27237958,27180212,27334931,27334805,27181256,27102742,27327377,27335339,27261468,27192343,27192113,27195515,27177298,27566120,27067760,27089413,26949924,27095818,27581933,27305589,27027666,27790574,27790483,27780328,27780321,27780318,26917114,27134318,27428478,27270689,27128721,26886746,26487344,27754286,26621370,27124697,24897961,27599558,27570900,27570899,27385474,27218221,27627024,27358314,27265297,26588452,27439883,27384073,27499423,27318892,27267317,27287825,27588522,27627971,27602560,27438995,27528097,27207059,27424951,27603379,26328537,26310971,26227907,27382013,27190210,27240529,26728569,26666206,26573769,26303664,27448177,27439991,27391680,27105708,27344942,27129805,26970394,27230882,27161376,27163190,27085606,27632386,27541742,27054437,26986747,26963050,26752124,27272768,27143602,27000940,27344000,27283360,27229759,27143622,27090742,27091613,27033969,26995794,28373806,28373800,26792786,27630522,27293050,27343365,27184235,27583831,27526987,27835727,26969413,27514296,27663830,27663826,27663804,27663803,27663801,27658836,27658835,27658834,27658832,27658831,27658829,26689706,26646576,26603624,27618460,27247171,27414748,27283263,27177973,27757131,27416139,27353541,27338296,27328999,26537838,27469022,27370017,27363702,27342643,28060978,27358492,27280452,27261492,27242348,27143795,27105902,27098066,27069064,27069063,27060129,27056715,26994397,26994115,26940700,26940699,26926831,26884547,25616504,27395767,26589391,26235751,25468180,25458857,25124519,25034760,25000913,27581658,27580934,27115528,27416820,27241318,27121259,27048265,27615702,27615701,27615700,27368152,27146275,27477199,27712719,28282077,28282074,27403591,27382989,27311987,27269479,27088656,26982812,26796250,27401667,27588034,27817844,27489386,27489383,27489381,27489379,27489377,27581816,26912606,27639287,27581454,27602389,27625619,27626030,27572077,27608522,27141854,27668176,27479923,27399308,27388803,27322868,27315458,27310922,27308721,27289325,27289213,27288735,27280525,27280523,27267440,27262087,27262086,27254652,27235985,27573041,27572938,27621706,27582711,27621717,27621713,28229104,27616989,27616987,27616996,27562545,27174656,27610074,27610072,27558472,27562238,27622139,27828700,27601904,27602386,27641567,27556394,27771104,27552340,27524619,27552816,27601987,27323834,27550615,27550864,27476602,27761358,27597820,27597833,27597832,27547853,27610299,27703469,27543610,27540164,27540162,27540161,27773354,27536773,27534796,27807566,27582690,27536336,27602387,27533410,27469163,27574475,27529679,26795442,26774963,26682468,26681495,26632269,26582588,26520240,26476593,26386481,27312422,27301679,27574527,27397081,27165761,27525806,27738379,27409727,27551696,27207913,27622135,27574431,27687477,27514778,27515535,27515430,27563287,27547037,27513670,27547036,27510506,27622140,27602385,27510902,27715317,27506236,27507689,27606053,27555813,27502473,27563237,27457931,27507650,27505231,27501933,27128179,27540314,27570623,27568887,27497284,27496180,27547191,27527489,28032012,27488170,27540379,27489090,27622137,27490164,27487316,27536254,27536253,27428477,27227402,27295028,27258654,27235578,27233217,27233215,27965857,27485325,27480492,27536115,27536110,27483382,27064142,26916502,26916628,27477140,27477133,27216261,26940805,27490835,27490832,27520922,27520921,27520913,27520912,27520910,27520904,27520901,27520898,27520896,27297803,26773690,27457138,27329645,27324147,26912469,26906441,26906437,26819405,27141430,26928870,27132765,27131780,27035065,26960162,27130439,27105834,26681496,27470381,27440233,27512585,27482034,26989099,26941264,27421791,27058163,26996305,26923065,27208492,27521670,27412729,27412728,27412727,27310240,27310227,27310225,27557033,27557029,27379654,27255405,27418328,27255726,26286079,27423360,27423354,27423346,27423345,27423341,28269451,28269178,28269167,28269013,28268815,28268598,28268527,28268424,28324996,27208815,27371030,27299655,27287808,25175055,25130368,27387589,27216588,27161263,27161262,27109327,26471517,27095442,27086499,26156083,27107764,26547434,26541835,26303414,26260899,26233432,26223428,26182894,27117554,26850904,27492885,27311104,27311102,27311101,27570908,27383213,27228319,27317683,27045414,27219475,28018124,27672485,27672484,26340849,27095414,27074803,27467223,27362488,27175984,27107261,26666550,27656561,27283386,27561152,27561151,27561148,27561145,27307187,27300251,27285659,27187561,26669716,27283129,27237551,27454042,27329682,27615048,26854361,26828824,26747063,26743313,26607477,27034067,27479612,27479611,27479610,27385472,27294319,27218222,27105458,27065105,27011310,26998695,26828911,26785057,27145766,27094177,26856328,27501180,27187935,26763784,26067156,27217590,27485911,27174400,27131617,27575859,26883319,26854755,27371496,27302942,27222269,27147592,27097730,26630458,27410165,27384424,27145361,27114251,27374147,27318812,27265549,27265548,27352936,27313112,27372868,27072164,27041387,27271499,26643540,26390827,26194183,27256556,27388526,27097547,27423796,27020041,27457686,27452837,27103065,27067126,26868058,26860202,26849714,26837462,26822489,26743859,26743857,27017941,27126805,27103375,27049594,26936087,26906930,27209485,27443356,27126217,27469238,26323598,26282453,27203278,27303024,27317386,27089985,27064663,26851573,27448253,27270050,27096221,27096220,27476901,26975523,26975522,27241961,27233756,27193328,27106560,27305830,27297048,27283122,27317020,27485931,25896792,26850023,27210727,27210726,27209527,27209526,27209525,27209524,27185483,27179666,27179665,27177808,27177807,27161760,27160791,27156239,27146475,27146474,27132495,27130563,27117677,27117676,27102424,27094718,27094717,27094716,27094715,27091656,27083780,27083779,27050477,27050475,27041675,27477243,27423133,26690856,26511676,26696378,27493717,27372610,27476869,27478487,27236087,27232552,27232551,27232550,27208512,27208511,27203153,27183105,27179694,27179693,27175910,27173659,27156032,27156031,27156027,27155286,27152905,27467100,27473529,27524962,26902949,27480675,27472964,26314508,28154637,27467081,27465466,27670776,27472366,27512370,27512369,27472373,27465803,27475632,27457404,27507940,27507958,27459408,27402753,27459725,27459724,27454214,27454213,27454212,27524901,27457306,27450676,27450328,27447922,27524884,27493627,27409810,27441598,27453425,27270122,27145294,27435909,27376413"}
    $.post("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=text&rettype=medline", id)
        .always(function(data, textStatus, jqXHR) { // See "Note 1" at the bottom about not including ".done"
            console.log(data);
        });

*/



