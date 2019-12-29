// map overlay: https://bl.ocks.org/mbostock/899711
// d3 v3 -> v4: https://amdevblog.wordpress.com/2016/07/20/update-d3-js-scripts-from-v3-to-v4/
// see https://developers.google.com/maps/documentation/javascript/customoverlays

var $ = jQuery;

// more console output 
var rrdebug = false;
var debugdetail = false;

// keep tip global
var tip;

// elevation mouseover focus configuration and definition
var dline = 13;
var xpos = 10;
var ypos = -5;
var padding = 2;
var boxwidth = 45;

// set up map overlay
var overlay, 
    mapwidth, 
    mapheight;

function initMap(width, height) {
    // Create the Google Map...
    var map = new google.maps.Map(d3.select("#runningroutes-route-map").node(), {
      zoom: 9,
      center: new google.maps.LatLng(39.431206, -77.415428),
      mapTypeId: google.maps.MapTypeId.TERRAIN,
      fullscreenControl: true
    });

    overlay = new SVGOverlayRoute(map, width, height);
};

$(document).ready(function() {
    // only execute on the route page
    if ($('#runningroutes-route-page').length == 0) return;

    SVGOverlayRoute.prototype = new google.maps.OverlayView();

    // initialize datatables and yadcf
    // set map div height - see https://stackoverflow.com/questions/1248081/get-the-browser-viewport-dimensions-with-javascript
    // 50% of viewport
    mapheight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0) * .67;
    mapwidth  = $("#runningroutes-route-map").width();
    $('#runningroutes-route-map').height( mapheight + 'px' );

    // do all the map stuff
    initMap( mapwidth, mapheight );

    var thisfid = urlParam('fileid');
    $("#path-title").text( urlParam('title') );

    descr = '<p>';
    if ( urlParam('descr') ) {
        descr += urlParam('descr');
    }
    if ( urlParam('gain') ) {
        if ( urlParam('descr') ) {
            descr += '<br/>';
        }
        descr +=  urlParam('gain') + 'ft elev gain';
    }
    if (descr !== '<p>') {
        descr += '</p>';
        $("#path-descr").append(descr);        
    }

    
    // gather parameters and return path for turns link
    var title = urlParam('title');
    var descrparam = urlParam('descr');
    var thisfid = urlParam('fileid');
    var gain = urlParam('gain');
    var turns = urlParam('turns');
    var thispath = window.location.pathname;
    var turnsurl = turns + '?' + setParams({
        title: title,
        fileid: thisfid,
        gain: gain,
        route: thispath,
    });

    // add turns link
    var $turnslink = $( "<a/>", {
        href: turnsurl, 
        text: 'turns',
    });
    $( '#turns-link' ).append( $turnslink );

    var progress = $("#progress-bar").progressbar({value: false});
    var progresslabel = $(".progress-label");

    // get data
    $.getJSON(runningroutesurl+"?op=path&fileid="+thisfid, function (data) {
        progress.progressbar("destroy");
        progresslabel.hide();

        // set up map
        overlay.setdata ( data.path );

        // set up elevation chart
        setelev ( data.path, overlay.dist() );
    });

});

// define SVGOverlayRoute class
/** @constructor */
function SVGOverlayRoute(map, width, height) {
    // Now initialize all properties.
    this.map = map;
    this.svg = null;
    this.path = null;
    this.data = [];
    this.height = height;
    this.width  = width;
    this.handleboundscheck = false;

    // TODO: set from cookie
    this.metric = false;

    this.onIdle = this.onIdle.bind(this);
    this.onPanZoom = this.onPanZoom.bind(this);

    // Explicitly call setMap on this overlay
    this.setMap(map);
}

SVGOverlayRoute.prototype.createsvg_ = function () {
    // configuration for d3-tip
    // TODO: remove this code if tip not needed
    tip = d3.tip()
            .direction('e')
            .offset([0,0])  // for now... what is this offset from?
            .attr("class", "d3-tip")
            // .attr("class", function(d) { "tip-" + d.loc })
            .html(function(d) { 
                var thistip = 'placeholder';
                return thistip;
            });

    this.svg = this.vis.append("svg")
                    .style("position", "absolute")
                    .style("top", 0 + "px")
                    .style("left", 0 + "px")
                    .style("width", this.width + "px")
                    .style("height", this.height + "px")
                    .attr("viewBox","0 0 " + this.width + " " + this.height)
                    .on("click", function() {
                        if (rrdebug) console.log('map clicked');
                        tip.hide();
                    });
    this.fullscreen = false;

    this.svg.call(tip);

    // set up mouseover
    this.focus = this.svg.append("g")
        .attr("id","focus-map")
        .classed("focus", true)
        .style("display", "none");
}

SVGOverlayRoute.prototype.onAdd = function () {
    if (rrdebug) console.log('onAdd()')
    // create runningroutes div
    // clearly this needs to be adjusted or this.svg should be appended to this layer
    var mappane = this.getPanes().overlayMouseTarget;
    var layer = d3.select(mappane).append("div")
        .attr("id", "runningroute-layer")
        .attr("class", "runningroute");

    this.vis = d3.select("#runningroute-layer");

    // create svg
    this.createsvg_()

    this.map.addListener('idle', this.onIdle);
    this.map.addListener('bounds_changed', this.onPanZoom);
    this.onPanZoom();
};

SVGOverlayRoute.prototype.fitbounds = function ( ) {
    // change bounds depending on data
    var lats = this.data.map(function(p) {return p[0]});
    var lngs = this.data.map(function(p) {return p[1]});
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/max
    var slat = lats.reduce(function(a,b) {return Math.min(a,b)});
    var nlat = lats.reduce(function(a,b) {return Math.max(a,b)});
    var elng = lngs.reduce(function(a,b) {return Math.max(a,b)});
    var wlng = lngs.reduce(function(a,b) {return Math.min(a,b)});
    this.map.fitBounds( { north: nlat, east: elng, south: slat, west: wlng } );

}

SVGOverlayRoute.prototype.setdata = function ( data ) {
    if (rrdebug) console.log('setdata()')
    this.data = data;
    var SVGOverlayRoute = this;

    // change bounds depending on data
    this.fitbounds();

    // create start, finish and mile icons
    this.addmarkers();

    this.draw();
};

// get current position
SVGOverlayRoute.prototype.getpos = function( createpos ) {
    // browser supports geolocation
    var iconsize = 100;
    var SVGOverlayRoute = this;  // remember for during getCurrentPosition callback

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function( position ) {
            SVGOverlayRoute.geolocationok = true;
            // elevation not required
            var currpos = [ position.coords.latitude, position.coords.longitude, 0 ];

            if ( createpos ){
                var posGenerator = d3.symbol().type(d3.symbolStar).size(iconsize);
                var posData = posGenerator();
                SVGOverlayRoute.pos = SVGOverlayRoute.svg.append("g")
                                .attr("d", currpos)
                                .classed("pos-marker", true)
                                .classed("route-marker", true);
                SVGOverlayRoute.pos.append('path')
                        .attr("d", posData);
                SVGOverlayRoute.onPanZoom();
            }

            // update position
            if (SVGOverlayRoute.pos) {
                SVGOverlayRoute.pos.attr("d", currpos)
                SVGOverlayRoute.onPanZoom();
            };

            console.log('getpos(): lat,lng = ' + currpos[0] + ',' + currpos[1]);
        }, 

        // error trying to get current position
        function() {
            console.log('geolocation service failed');
        });

    //browser doesn't support geolocation
    } else {
        console.log('browser doesn\'t support geolocation');
    }
}

// create start, finish and mile/km icons
SVGOverlayRoute.prototype.addmarkers = function() {
    // http://d3indepth.com/shapes/#symbols
    var iconsize = 250;
    var startGenerator = d3.symbol().type(d3.symbolTriangle).size(iconsize);
    var startData = startGenerator();
    var endGenerator = d3.symbol().type(d3.symbolSquare).size(iconsize);
    var endData = endGenerator();
    var distGenerator = d3.symbol().type(d3.symbolSquare).size(iconsize);
    var distData = distGenerator();

    // start marker
    var startpoint = this.data[0];
    var start = this.svg.append("g")
                    .attr("d", startpoint)
                    .classed("start-marker", true)
                    .classed("route-marker", true);
    start.append('path')
            .attr("d", startData)
            .attr("transform", "rotate(90)");

    // end marker
    var endpoint   = this.data[this.data.length-1];
    var end = this.svg.append("g")
                    .attr("d", endpoint)
                    .classed("end-marker", true)
                    .classed("route-marker", true);
    end.append('path')
            .attr("d", endData);

    // position marker
    this.geolocationok = false;
    this.getpos( true );
    var SVGOverlayRoute = this;
    // update position every 5 seconds
    this.postimer = setInterval(function(){ SVGOverlayRoute.getpos( false ) }, 5000);

    // mile / km markers
    this._dist = [];
    this._dist.push(0);
    var dist = 0;
    var lastmarker = 0;
    var isMiles = !this.metric;
    // start at 2nd coordinate (index 1)
    if (debugdetail) console.log('i,lat1,lng1,ele1,lat2,lng2,ele2,dist')
    for (var i=1; i<this.data.length; i++) {
        dist += haversineDistance(this.data[i-1], this.data[i], isMiles);
        this._dist.push(dist);
        if (debugdetail) console.log(i + ',' + this.data[i-1] + ',' + this.data[i] + ',' + dist);
        var intdist = Math.trunc(dist);
        if ( intdist != lastmarker ) {
            lastmarker = intdist;
            var distpoint   = this.data[i];
            var distel = this.svg.append("g")
                            .attr("d", distpoint)
                            .classed("distance-marker", true)
                            .classed("route-marker", true);
            distel.append('path')
                    .attr("d", distData)
                    .attr("transform", "rotate(45)");
            distel.append('text')
                    .classed('distance-text', true)
                    .attr("text-anchor", "middle")
                    .attr("transform", "translate(0,3.5)")
                    .text(intdist);
        }
    }
}

SVGOverlayRoute.prototype.sethandleboundscheck = function( val ) {
    this.handleboundscheck = val;
};

// handles pan and zoom, and also handles change to/from full screen
SVGOverlayRoute.prototype.onPanZoom = function () {
    if (rrdebug) console.log('onPanZoom()')
    var proj = this.getProjection();
    var SVGOverlayRoute = this;  // for use within d3 functions

    if (this.path) {
        this.path.remove();
    }

    // add route path
    // https://www.dashingd3js.com/svg-paths-and-d3js
    // https://github.com/d3/d3-geo/blob/master/README.md#geoPath
    // https://stackoverflow.com/questions/43196140/google-maps-with-d3-paths-as-a-layer-using-d3-v4
    this.path = this.svg.append("path")
            .attr("d", pathFunction(this.data))
            .attr("stroke", "blue")
            .attr("stroke-width", 2 + "px")
            .attr("fill", "none")
            .classed("path", true);

    this.svg.selectAll('.route-marker')
                    .attr("transform", function() { 
                        return "translate(" +
                            SVGOverlayRoute.transform( d3.select(this).attr("d").split(",") ).x +
                            "," +
                            SVGOverlayRoute.transform( d3.select(this).attr("d").split(",") ).y +
                            ")"
                        })
                    .raise();
    //     .attr("cx", function(d) { return SVGOverlayRoute.transform( d ).x })
    //     .attr("cy", function(d) { return SVGOverlayRoute.transform( d ).y });

    // reset svg location and size
    this.bounds = this.map.getBounds();
    var nebounds = this.bounds.getNorthEast();
    var swbounds = this.bounds.getSouthWest();
    var svgx = Math.round( this.transform( [nebounds.lat(), swbounds.lng()] ).x );
    var svgy = Math.round( this.transform( [nebounds.lat(), swbounds.lng()] ).y );

    // determine height / width based on whether fullscreen or not
    // see https://stackoverflow.com/questions/39620850/google-maps-api-v3-how-to-detect-when-map-changes-to-full-screen-mode
    var width, height;
    // if fullscreen now
    if ( $(this.map.getDiv()).children().eq(0).height() == window.innerHeight &&
         $(this.map.getDiv()).children().eq(0).width()  == window.innerWidth ) {
        if (rrdebug) console.log( 'FULL SCREEN' );
        width = window.innerWidth;
        height = window.innerHeight;

        // change in state, refit bounds [not working]
        // if (!this.fullscreen) {
        //     this.fitbounds();
        // }
        // this.fullscreen = true;
    }
    else {
        if (rrdebug) console.log ('NOT FULL SCREEN');
        width = this.width;
        height = this.height;

        // change in screen state, refit bounds [not working]
        // if (this.fullscreen) {
        //     this.fitbounds()
        // }
        // this.fullscreen = false;
    }

    // reset svg attributes
    this.svg
        .style("left", svgx + "px")
        .style("top", svgy + "px")
        .style("width", width + "px")
        .style("height", height + "px")
        .attr("viewBox",svgx + " " + svgy + " " + width + " " + height);
};

SVGOverlayRoute.prototype.onIdle = function() {
    if (rrdebug) console.log('idle event fired');

    // when do we start doing this? After first draw, I think
    if (this.handleboundscheck) {
        // filter table to show only routes within the rendered map view
        this.bounds = this.map.getBounds();
        var nebounds = this.bounds.getNorthEast();
        var swbounds = this.bounds.getSouthWest();
        var lowlat = Math.min(nebounds.lat(), swbounds.lat());
        var lowlng = Math.min(nebounds.lng(), swbounds.lng());
        var hilat  = Math.max(nebounds.lat(), swbounds.lat());
        var hilng  = Math.max(nebounds.lng(), swbounds.lng());
        if (rrdebug) console.log ('(lowlat, hilat, lowlng, hilng) = ' + lowlat + ', ' + hilat + ', ' + lowlng + ', ' + hilng );
    };
}

SVGOverlayRoute.prototype.onRemove = function () {
    this.map.removeListener('bounds_changed', this.onPanZoom);
    this.svg.remove();
    this.svg = null;
};

SVGOverlayRoute.prototype.draw = function () {
    if (rrdebug) console.log('draw');

    // nothing to do if onAdd hasn't been called yet
    if (!this.svg) return;

    // for use within d3 functions, may need to class instance that we're in
    var SVGOverlayRoute = this;  

    // add path and update point locations
    this.onPanZoom();
};

// transform point from [lat, lng] to google.maps.Point
SVGOverlayRoute.prototype.transform = function( p ) {
    var latlng = new google.maps.LatLng( p[0], p[1] );
    var proj = this.getProjection();
    return proj.fromLatLngToDivPixel(latlng)
};

// get distance array
SVGOverlayRoute.prototype.dist = function( ) {
    return this._dist;
}

// mousemove handler
SVGOverlayRoute.prototype.mousemove = function( lat, lng ) {
    var d = [lat, lng];
    var xmouse = this.transform(d).x;
    var ymouse = this.transform(d).y;
    this.focus.attr("transform", "translate(" + xmouse + "," + ymouse + ")").raise();
}

// access path data
// https://www.dashingd3js.com/svg-paths-and-d3js
// this may be a klunky way to do this, but does it work?
pathFunction = d3.line()
        .x(function(d) { return overlay.transform(d).x})
        .y(function(d) { return overlay.transform(d).y});

// set elevation chart
//  path - array of [lat, lng, ele]
//  dist - array of accumulated_distance 
function setelev( path, dist ) {
    if (path.length != dist.length ) throw "parameter mismatch";

    // combine path and dist data
    eledata = [];
    for (var i=0; i<path.length; i++) {
        eledata.push({
            lat: path[i][0],
            lng: path[i][1],
            ele: path[i][2],
            dist: dist[i]
        });
    }

    // calculate elevation height, width
    var eleheight = mapheight*.4,
        elewidth  = mapwidth;
    var svg = d3.select("#runningroutes-route-elev").append("svg")
            .attr("width", elewidth+'px')
            .attr("height", eleheight+'px');
    var margin = {top: 20, right: 70, bottom: 30, left: 50},
        width = +elewidth - margin.left - margin.right,
        height = +eleheight - margin.top - margin.bottom,
        g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var mouseoverlay = g.append("rect")
        .attr("class", "overlay")
        .attr("width", width + margin.right)
        .attr("height", height + margin.bottom);

    var x = d3.scaleLinear()
        .rangeRound([0, width]);

    var y = d3.scaleLinear()
        .rangeRound([height, 0]);

    x.domain(d3.extent(eledata, function(d) { return d.dist; }));
    y.domain(d3.extent(eledata, function(d) { return d.ele; }));

    var line = d3.line()
                .x(function(d) { return x(d.dist); })
                .y(function(d) { return y(d.ele); });

    g.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));
      // .select(".domain")
      //   .remove();
  
    g.append("g")
        .call(d3.axisLeft(y))
      .append("text")
        .attr("fill", "#000")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", "0.71em")
        .attr("text-anchor", "end")
        .text("Elevation (ft)");
  
    g.append("path")
        .datum(eledata)
        .classed('line', true)
        .attr("fill", "none")
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("d", line);

    var thisfocus = svg.append("g")
        .attr("id","focus")
        .classed("focus", true)
        .style("display", "none");

    // this also affects map mouseover
    var allfocus = d3.selectAll(".focus");
    allfocus.append("rect")
        .attr("height", (2*(dline+padding)) + 'px')
        .attr("width", boxwidth+"px")
        .attr("x", (xpos-padding)+"px")
        .attr("y", (ypos-10-padding)+"px") // why doesn't ypos work?
        .classed("focus-background", true);

    allfocus.append("circle")
        .attr("r", 4.5);

    var text = allfocus.append("text")
        .style("text-anchor", "start")
        .attr("x", 4+"px")
        .attr("y", 7+"px")
        .attr("dy", ".35em");
    text.append('tspan')
        .attr('x', xpos+"px")
        .attr('y', ypos+"px")
        .attr('dy', '0px')
        .classed('focus-dist', true);
    text.append('tspan')
        .attr('x', xpos+"px")
        .attr('y', ypos+"px")
        .attr('dy', 1*dline+'px')
        .classed('focus-ele', true);

    mouseoverlay
      .on("mouseover", function() { mousein() })
      .on("mouseout", function() { mouseout() })
      .on("mousemove", mousemove);

    var bisectDist = d3.bisector(function(d) { return d.dist; }).left;
  
    function mousein() {
        allfocus.style("display", null);
    }

    function mouseout() {
        allfocus.style("display", "none");
    }

    function mousemove() {
        var x0 = x.invert(d3.mouse(this)[0]);
        var i = bisectDist(eledata, x0, 1);
        var d = i < eledata.length ? eledata[i] : eledata[eledata.length-1];

        var thisfocus = d3.select("#focus");
        var xmouse = x(d.dist)+margin.left;
        var ymouse = y(d.ele)+margin.top;
        thisfocus.attr("transform", "translate(" + xmouse + "," + ymouse + ")");
        overlay.mousemove(d.lat, d.lng);

        d3.selectAll('.focus-dist').text(d.dist.toFixed(2) + "M");
        d3.selectAll('.focus-ele').text(d.ele + "'");
    }

}