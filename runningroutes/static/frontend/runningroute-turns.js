var $ = jQuery;

var turns = [];
var fulllist; 

// configuration of grid widget
var gridrows = 6, gridcols = 4;

// track last state for grid widget
// todo make the grid stuff into a class
var lastrowx = 0, 
    lastcolx = 0;

// more console output when rrdebug = true
var rrdebug = true;

// fill in grid widget
var gridtable = $( "<table/>", { class: "grid-select" });
for (var rowx=0; rowx<gridrows; rowx++) {
    var thisrow = $( "<tr/>");
    for (var colx=0; colx<gridcols; colx++) {
        var thiscell = $( "<td/>")
        // it is ok to assume rowx and colx are both single digits
        thiscell.attr("id", "gridcell"+rowx+colx); 
        thiscell.addClass("gridcell").attr("rowx", rowx).attr("colx", colx);
        thiscell.on("mouseover", showgridval);
        thiscell.on("click", setgridval);

        thiscell.appendTo(thisrow);
    }
    thisrow.appendTo(gridtable);
};
var griddialog = $( "#grid-dialog" );
griddialog.append(gridtable);

// https://stackoverflow.com/questions/12744928/in-jquery-how-can-i-set-top-left-properties-of-an-element-with-position-values
var gridwidget = $( "#turn-grid-widget");
griddialog.parent().css({position: 'relative'});
griddialog.css({top: gridwidget.position().top+gridwidget.height()/2, 
                left: gridwidget.position().left+gridwidget.width(), 
                position:'absolute'});
griddialog.hide();


$(document).ready(function() {
    var title = urlParam('title');
    var thisfid = urlParam('fileid');

    // gather parameters and return path for route link
    var descrparam = urlParam('descr')
    var gain = urlParam('gain');
    var route = urlParam('route');
    var thispath = window.location.pathname;
    console.log('thispath='+thispath);
    var routeurl = route + '?' + setParams({
        title: title,
        fileid: thisfid,
        gain: gain,
        turns: thispath,
    });

    // add route link
    var $routelink = $( "<a/>", {
        href: routeurl, 
        text: 'route',
    });
    $( '#route-link' ).append( $routelink );

    $("#turn-title").text(title);
    var progress = $("#progress-bar").progressbar({value: false});
    var progresslabel = $(".progress-label");

    $.getJSON(rrturnsurl+"?op=turns&fileid="+thisfid, function (data) {
        progress.progressbar("destroy");
        progresslabel.hide();

        $.each( data.turns, function ( key, turn ) {
            turns.push("<li>" + turn + "</li>");
        });

        fulllist = $( "<ul/>", {
            class: "turn-list",
            html: turns.join("\n")
        });

        // initial condition 1x1
        setgrid(1, 1);
    });

});

function setgrid(rows, cols){
    $( ".turn-row" ).remove();

    var td = $("<td/>").append(fulllist.clone());
    var tr = $("<tr/>", { class: "turn-row" });
    for (var i=0; i<cols; i++) {
        tr.append(td.clone())
    }
    var table = $( "<table/>")
    for (var i=0; i<rows; i++) {
        table.append(tr.clone());
    }

    table.appendTo("#turn-table");
};

function togglebullets() {
    var ul = $( ".turn-list" );

    // if nobullets is indicated, remove class
    if (fulllist.hasClass("nobullets")) {
        fulllist.removeClass("nobullets");
        ul.removeClass("nobullets");
    } else {
        fulllist.addClass("nobullets");
        ul.addClass("nobullets");
    }
}

function togglehighlighted() {
    var ul = $( ".turn-list" );

    // if highlighted is indicated, remove class
    if (fulllist.hasClass("highlighted")) {
        fulllist.removeClass("highlighted");
        ul.removeClass("highlighted");
    } else {
        fulllist.addClass("highlighted");
        ul.addClass("highlighted");
    }
}

function togglegrid() {
    if (griddialog.hasClass("visible")) {
        griddialog.hide();
        griddialog.removeClass("visible");
        setactivegrid(lastrowx, lastcolx);
    } else {
        griddialog.show();
        griddialog.addClass("visible");
    }
}

function setactivegrid(thisrowx, thiscolx) {
    for (var rowx=0; rowx<gridrows; rowx++) {
        for (var colx=0; colx<gridcols; colx++) {
            if (rowx<=thisrowx && colx<=thiscolx) {
                // it is ok to assume rowx and colx are both single digits
                $( "#gridcell" + rowx + colx).addClass("active");
            } else {
                $( "#gridcell" + rowx + colx).removeClass("active");
            }
        }
    }
}

function showgridval() {
    var thisrowx = +$(this).attr("rowx");
    var thiscolx = +$(this).attr("colx");
    if (rrdebug) console.log("showgridval() " + thisrowx + " " + thiscolx);

    setactivegrid(thisrowx, thiscolx);
};

function setgridval() {
    var rowx = +$(this).attr("rowx");
    var colx = +$(this).attr("colx");
    if (rrdebug) console.log("setgridval() " + rowx + " " + colx);
    griddialog.hide();
    griddialog.removeClass("visible");
    setgrid (rowx+1, colx+1);
    lastrowx = rowx;
    lastcolx = colx;
};