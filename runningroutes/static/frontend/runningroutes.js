// map overlay: https://bl.ocks.org/mbostock/899711
// d3 v3 -> v4: https://amdevblog.wordpress.com/2016/07/20/update-d3-js-scripts-from-v3-to-v4/
// see https://developers.google.com/maps/documentation/javascript/customoverlays

$(function() {
    // only execute on the main table page
    if ($('#rr-table-page')) {
        // more console output when debug = true
        var rrdebug = true;

        // for metadata within row
        var loc2id = {},
            id2loc = {};

        // keep tip global
        var tip;

        // options for datatables
        var myTable;
        var datatables_options = {
            // "order": [[1,'asc']],
            dom: '<"clear">lBfrtip',
            ajax: {
                   // runningroutesurl is defined in in wp-content/themes/steeps/js/runningroutes directory locally
                   // configured runningroutes-config.js
                   // TODO: what URL, where does it come from?
                   url: runningroutesurl+"?op=routes",
                   dataSrc: 'features',
                  },
            columns: [
                { name: 'loc',      data: 'loc',  className: "dt-body-center", defaultContent: '' },  // set in preDraw
                { name: 'name',     data: 'geometry.properties.name' },
                { name: 'distance', data: 'geometry.properties.distance',  className: "dt-body-center"},
                { name: 'surface',  data: 'geometry.properties.surface',  className: "dt-body-center" },
                { name: 'gain',     data: 'geometry.properties.gain',  className: "dt-body-center", defaultContent: '' },
                { name: 'links',    data: 'geometry.properties.links', orderable: false, render: function(data, type, row, meta) {
                    var props = row.geometry.properties;
                    var links = buildlinks(props, ' ');
                    return links;
                } },
                { name: 'lat',      data: 'geometry.properties.lat', visible: false },
                { name: 'lng',      data: 'geometry.properties.lng', visible: false },
                { name: 'id',       data: 'geometry.properties.id', visible: false },
            ],
            rowCallback: function( row, thisd, index ) {
                var thisid = thisd.geometry.properties.id;
                $(row).attr('rowid', thisid);
            },
            buttons: ['csv'],
        }

        // options for yadcf
        var distcol = 2,
            surfacecol = 3,
            latcol = 6,
            lngcol = 7;
        var yadcf_options = [
                  { column_number: distcol,
                    filter_type: 'range_number',
                    filter_container_id: 'external-filter-distance',
                  },
                  { column_number: surfacecol,
                    filter_container_id: 'external-filter-surface',
                  },
                  { column_number: latcol,
                    filter_type: 'range_number',
                    filter_container_id: 'external-filter-bounds-lat',
                  },
                  { column_number: lngcol,
                    filter_type: 'range_number',
                    filter_container_id: 'external-filter-bounds-lng',
                  },
            ];

        // configuration for map display
        var rcircle = 10,
            rcircleselected = 1.5 * rcircle,
            pi = Math.PI,
            dexpmin = rcircle * 4,    // minimum distance for explosion
            maxroutes = 40,           // maximum number of routes handled for non-overlapping explosion
            separation = 3,           // number of pixels to separate individual routes during explosion
            dexpmax = maxroutes * (rcircle + separation) / (2*pi),
            durt = 500,   // transition duration (msec)
            textdy = 4,   // a bit of a hack, trial and error
            // padding is from center of circle
            padding = rcircleselected + 2, // +2 adjusts for circle stroke width
            t = d3.transition(durt);

        // set up map overlay
        var overlay,
            mapwidth,
            mapheight;
        SVGOverlay.prototype = new google.maps.OverlayView();

        function initMap(width, height) {
            // Create the Google Map...
            var map = new google.maps.Map(d3.select("#runningroutes-map").node(), {
              zoom: 9,
              center: new google.maps.LatLng(39.431206, -77.415428),
              mapTypeId: google.maps.MapTypeId.TERRAIN,
              fullscreenControl: false
            });

            overlay = new SVGOverlay(map, width, height);
        };


        $(document).ready(function() {
            // initialize datatables and yadcf
            myTable = $("#runningroutes-table").DataTable(datatables_options);
            yadcf.init(myTable, yadcf_options);

            // set map div height - see https://stackoverflow.com/questions/1248081/get-the-browser-viewport-dimensions-with-javascript
            // 50% of viewport
            mapheight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0) * .5;
            mapwidth  = $("#runningroutes-map").width();
            $('#runningroutes-map').height( mapheight + 'px' );

            // do all the map stuff
            initMap( mapwidth, mapheight );

            var justpaging = false;
            myTable.on('page.dt', function() {
                justpaging = true;
            });

            var justsorting = false;
            myTable.on( 'preDraw.dt', function() {
                // As preDraw actions happen after the sort in dataTables, a second draw is required.
                // The 'justsorting' draw was invoked at the bottom of the draw.dt function just to sort the table
                if (justsorting) return;

                // don't want to do all this if we're just paging
                if (justpaging) return;

                // get filtered data from datatables
                // datatables data() method extraneous information, just pull out the data
                var dtdata = myTable.rows( { search: 'applied' } ).data();
                var data = [];
                for (var i=0; i<dtdata.length; i++) {
                    data.push(dtdata[i])
                };

                // set up loc metadata within data
                loc2id = {};
                for (var i=0; i<data.length; i++) {
                    var d = data[i];    // get convenient handle
                    var thisid = d.geometry.properties.id;
                    var key = d.geometry.properties.latlng;
                    if (loc2id[key] === undefined) {
                        loc2id[key] = [];
                    };
                    // convenient to save data index rather than id
                    loc2id[key].push(thisid);
                };

                // TODO: sort locations somehow - by distance from Frederick center? from center of map?
                var locations = Object.keys(loc2id);
                locations.sort().reverse();   // currently north to south because key is lat,lng, northern hemi
                id2loc = {};
                // loop thru locations
                for (var i=0; i<locations.length; i++) {
                    var thisloc = i+1;      // locations are 1-based
                    // loop thru routes at this location
                    var key = locations[i];
                    for (var j=0; j<loc2id[key].length; j++) {
                        var thisid = loc2id[key][j];
                        id2loc[thisid] = thisloc;
                        if (rrdebug) console.log('preDraw: id2loc['+thisid+'] = ' + thisloc);
                    };
                };

                // update loc cell in the table
                myTable.rows( { search: 'applied' } ).every ( function (i, tblloop, rowloop) {
                    var thisid = this.data().geometry.properties.id;
                    // loc is 0th column in the row
                    var dloc = id2loc[thisid];
                    myTable.cell({row: i, column: 0}).data(dloc);

                });

                // also update the data array
                for (var i=0; i<data.length; i++) {
                    var thisid = data[i].geometry.properties.id;
                    var dloc = id2loc[thisid];
                    data[i].loc = dloc;
                    data[i].id  = thisid;
                };

                // tell the map about it
                overlay.setdata ( data );
            });

            var firstdraw = true;
            myTable.on( 'draw.dt', function() {

                // As preDraw actions happen after the sort in dataTables, a second draw is required.
                // The 'justsorting' draw was invoked at the bottom of this function just to sort the table
                if (justsorting) {
                    if (rrdebug) console.log('draw.dt event, just sorting');
                    justsorting = false;
                    return;
                }

                // don't want to do all this if we're just paging
                if (justpaging) {
                    if (rrdebug) console.log('draw.dt event, just paging');
                    justpaging = false;
                    return;
                };

                if (rrdebug) console.log('draw.dt event');

                // handle mouseover events for table rows
                $("#runningroutes-table tr").not(':first').mouseenter(function(){
                    // highlight table
                    $( this ).css("background-color", "yellow");

                    // find all interesting elements
                    var thisid = $( this ).attr('rowid');
                    var circle = $("#route-circle-" + thisid);
                    var group = circle.parent();
                    var svg = group.parent();
                    var routes = svg.parent();

                    // highlight the circle
                    circle.attr("r", rcircleselected);

                    // bring containing group to top - see https://stackoverflow.com/questions/14120232/svg-elements-overlapping-issue
                    svg.append(group);
                });

                // handle mouseover events for table rows
                $("tr").not(':first').mouseleave(function(){
                    // unhighlight table
                    $( this ).css("background-color", "");

                    // find interesting elements
                    var thisid = $( this ).attr('rowid');
                    var circle = $("#route-circle-" + thisid);

                    // unhighlight the circle
                    circle.attr("r", rcircle);
                });


                // zoom to current bounds and handle map bounds check after first draw
                if (firstdraw) {
                    firstdraw = false;
                    overlay.zoomtobounds();
                    overlay.sethandleboundscheck(true);
                };

                // if not justsorting, draw again to sort
                justsorting = true;
                myTable.draw();
            });
        });

        // define SVGOverlay class
        /** @constructor */
        function SVGOverlay(map, width, height) {
            // Now initialize all properties.
            this.map = map;
            this.svg = null;
            this.data = [];
            this.height = height;
            this.width  = width;
            this.handleboundscheck = false;

            this.onIdle = this.onIdle.bind(this);
            this.onPanZoom = this.onPanZoom.bind(this);

            // Explicitly call setMap on this overlay
            this.setMap(map);
        }

        SVGOverlay.prototype.createsvg_ = function () {
            // configuration for d3-tip
            tip = d3.tip()
                    .direction('e')
                    .offset([0,rcircle+1])
                    .attr("class", "d3-tip")
                    // .attr("class", function(d) { "tip-" + d.loc })
                    .html(function(d) {
                        var dd = d.geometry.properties;
                        var thistip = dd.name;
                        thistip += "<br/>" + dd.distance + " miles (" + dd.surface + ")";
                        if (dd.description)
                            thistip += "<br/>" + dd.description;
                        if (dd.gain)
                            thistip += "<br/>" + dd.gain + " ft elev gain";
                        thistip += "<br/>" + buildlinks(dd, ', ');
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

            this.svg.call(tip);
        }

        SVGOverlay.prototype.onAdd = function () {
            if (rrdebug) console.log('onAdd()')
            // create runningroutes div
            // clearly this needs to be adjusted or this.svg should be appended to this layer
            var mappane = this.getPanes().overlayMouseTarget;
            var layer = d3.select(mappane).append("div")
                .attr("id", "runningroutes-layer")
                .attr("class", "runningroutes");

            this.vis = d3.select("#runningroutes-layer");

            // create svg
            this.createsvg_()

            this.map.addListener('idle', this.onIdle);
            this.map.addListener('bounds_changed', this.onPanZoom);
            this.onPanZoom();
        };

        SVGOverlay.prototype.setdata = function ( data ) {
            if (rrdebug) console.log('setdata()')
            this.data = data;

            this.draw();
        };

        SVGOverlay.prototype.zoomtobounds = function ( ) {
            // change bounds depending on data
            var lats = this.data.map(function(p) {return p.geometry.coordinates[0]});
            var lngs = this.data.map(function(p) {return p.geometry.coordinates[1]});
            // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/max
            var slat = lats.reduce(function(a,b) {return Math.min(a,b)});
            var nlat = lats.reduce(function(a,b) {return Math.max(a,b)});
            var elng = lngs.reduce(function(a,b) {return Math.max(a,b)});
            var wlng = lngs.reduce(function(a,b) {return Math.min(a,b)});
            this.map.fitBounds( { north: nlat, east: elng, south: slat, west: wlng } );
        }

        SVGOverlay.prototype.sethandleboundscheck = function ( val ) {
            this.handleboundscheck = val;
        };

        SVGOverlay.prototype.onPanZoom = function () {
            if (rrdebug) console.log('onPanZoom()')
            var proj = this.getProjection();
            var svgoverlay = this;  // for use within d3 functions

            // collapse any exploded locations
            d3.selectAll(".handle").each(unexplodeData);

            this.svg.selectAll('.route')
              // .data(this.data, function(d) { return d.id })
                .attr('cx', function(d) { return svgoverlay.transform( d.geometry.coordinates ).x })
                .attr('cy', function(d) { return svgoverlay.transform( d.geometry.coordinates ).y })
                .attr("class", function(d) { return "g-loc-" + d.loc; })    // overwrites class so must be before classed()
                .classed("route", true);

            this.svg.selectAll('.route-circle')
              // .data(this.data, function(d) { return d.id })
                .attr("r", rcircle)
                .attr("cx", function(d) { return svgoverlay.transform( d.geometry.coordinates ).x })
                .attr("cy", function(d) { return svgoverlay.transform( d.geometry.coordinates ).y })
                .attr("id", function(d) { return 'route-circle-' + d.id })
                .attr("class", function(d) { return "c-loc-" + d.loc; })
                .classed("route-circle", true);

            this.svg.selectAll('.route-text')
              // .data(this.data, function(d) { return d.id })
                .attr("x", function(d) { return svgoverlay.transform( d.geometry.coordinates ).x })
                .attr("y", function(d) { return svgoverlay.transform( d.geometry.coordinates ).y })
                .attr("text-anchor", "middle")
                .attr("dy", function(d) { return textdy })
                .attr("class", function(d) { return "t-loc-" + d.loc; })
                .classed("route-text", true)
                .text(function(d) { return d.loc; });

            // reset svg location
            this.bounds = this.map.getBounds();
            var nebounds = this.bounds.getNorthEast();
            var swbounds = this.bounds.getSouthWest();
            var svgx = Math.round( this.transform( [nebounds.lat(), swbounds.lng()] ).x );
            var svgy = Math.round( this.transform( [nebounds.lat(), swbounds.lng()] ).y );
            this.svg
                .style("left", svgx + "px")
                .style("top", svgy + "px")
                // .attr("transform", "translate(" + -svgx + "," + -svgy + ")")
                .attr("viewBox",svgx + " " + svgy + " " + this.width + " " + this.height);
        };

        SVGOverlay.prototype.onIdle = function() {
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
                // not clear why I need to add third parameter here, but not in https://codepen.io/louking/pen/EbKYJd
                yadcf.exFilterColumn(myTable, [[latcol, {from: lowlat, to: hilat}], [lngcol,  {from: lowlng, to: hilng}]], true);
            };
        }

        SVGOverlay.prototype.onRemove = function () {
            this.map.removeListener('bounds_changed', this.onPanZoom);
            this.svg.remove();
            this.svg = null;
        };

        SVGOverlay.prototype.draw = function () {
            if (rrdebug) console.log('draw');

            // nothing to do if onAdd hasn't been called yet
            if (!this.svg) return;

            // for use within d3 functions, may need to class instance that we're in
            var svgoverlay = this;

            // select all starting points
            // Add group containers to hold circle and text
            var routes = this.svg.selectAll("g")
                  .data(this.data, function(d) { return d.id });

            routes.enter().append("g")
                    // .call(entering)
                    .classed("route", true)
                    .attr("transform", "translate(0,0)")
                    .style("cursor", "pointer")
                    .on("click", explodeData);

            routes.exit()
                  // .call(exiting)
                  .remove();

            // Add a circle and text to all existing routes, if not there already
            d3.selectAll(".route").each(function(d, i) {
                var thisroute = d3.select(this);
                if (thisroute.select("circle").empty()) {
                    thisroute.append("circle").classed("route-circle", true);
                }
                if (thisroute.select("text").empty()) {
                    thisroute.append("text").classed("route-text", true);
                }
            })

            // update point locations
            this.onPanZoom();
        };

        // transform point from [lat, lng] to google.maps.Point
        SVGOverlay.prototype.transform = function( p ) {
            var latlng = new google.maps.LatLng( p[0], p[1] );
            var proj = this.getProjection();
            return proj.fromLatLngToDivPixel(latlng)
        };

        // called with group containing circle, text
        // if there are other groups in same location, explode
        // else special handling for lone group
        function explodeData(d, i) {
          // Use D3 to select element and also all at same location
          var loc = d.loc;
          var thisg = d3.select(this);
          var theselocs = d3.selectAll(".g-loc-" + loc)
          var numlocs = theselocs.size();
          var svg = d3.select(this.parentNode);

          // shouldn't happen
          if (numlocs == 0) {
            throw 'noLocationsFound';

          // if only one at location, maybe there is some special processing
          } else if (numlocs == 1) {
            // handle single selection click
            // don't let this through to svg click event
            // http://bl.ocks.org/jasondavies/3186840
            d3.event.stopPropagation();
            tip.show(d);

          // multiple at location, explode
          } else {
            // if not selected yet, explode all in same loc
            if (!thisg.attr("exploded")) {
              // d3.select(this).raise();
              theselocs.attr("exploded", true);
              var cx = Number(thisg.attr("cx"));
              var cy = Number(thisg.attr("cy"));

              // create lines now so they're underneath
              // initially x1,y1 = x2,y2 because we'll be transitioning
              theselocs.each(function (d,i) {
                svg.append('line')
                    .attr("class", "l-loc-" + loc)
                    .attr("x1", cx)
                    .attr("y1", cy)
                    .attr("x2", cx)
                    .attr("y2", cy)
                    .attr("stroke-width", 1.5)
                    .attr("stroke", "black")
                  .transition(t)
                    .attr("x2", cx + dexp(numlocs) * Math.cos((2*pi/numlocs)*i))
                    .attr("y2", cy + dexp(numlocs) * Math.sin((2*pi/numlocs)*i))
              });

              // create handle for original location
              svg.append("circle")
                .attr("id", "exploded-" + loc)
                .attr("class", "handle")
                .attr("loc", d.loc)
                .attr("r", rcircle)
                .attr("cx", cx)
                .attr("cy", cy)
                .style("cursor", "pointer")
                .on("click", unexplodeData);

              // explode
              theselocs
                .each(function(d, i){
                  var thisg = d3.select(this);

                  // transition to new location
                  thisg.raise().transition(t)
                    .attr("transform", "translate("
                          + dexp(numlocs) * Math.cos((2*pi/numlocs)*i) + ","
                          + dexp(numlocs) * Math.sin((2*pi/numlocs)*i) + ")"
                          );
                });

              // if exploded and individual selected, maybe there is some special processing
            } else {
              // handle single selection click
              // don't let this through to svg click event
              // http://bl.ocks.org/jasondavies/3186840
              d3.event.stopPropagation();
              tip.show(d);
            }

          } // multiple at location
        };

        // called with handle for an exploded group
        function unexplodeData(d, i) {
          // Use D3 to select element
          var handle = d3.select(this);
          var loc = handle.attr("loc");
          var x = handle.attr("cx");
          var y = handle.attr("cy");
          var theselocs = d3.selectAll(".g-loc-" + loc);

          // set exploded circles to original state
          theselocs.transition(t)
              .attr("selected", null)
              .attr("transform", "translate(0,0)")
              .attr("exploded", null);

          // shrink lines
          d3.selectAll(".l-loc-" + loc)
            .transition(t)
              .attr("x2", x)
              .attr("y2", y)
              .remove()

          // remove handle
          d3.select("#exploded-" + loc).remove();

        };

        // build links for map, table
        function buildlinks(props, separator) {
            var links = [];
            // start link
            links.push('<a href="https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(props.start) + '" target=_blank>start</a>');

            // map link
            // display our own map?
            if (props.fileid) {
                // rrrouteurl is defined in in wp-content/themes/steeps/js/runningroutes directory locally
                // configured runningroutes-config.js
                // TODO: some surgery required here for new data schema
                var thislink = '<a href="' + rrrouteurl + '?title=' + encodeURIComponent(props.name + ' - '
                                + props.distance + ' miles - ' + props.surface)
                                + '&fileid=' + props.fileid;
                if (props.description)
                    thislink += '&descr=' + encodeURIComponent(props.description);
                if (props.gain)
                    thislink += '&gain=' + encodeURIComponent(props.gain);
                // rrturnsurl is defined in in wp-content/themes/steeps/js/runningroutes directory locally
                // configured runningroutes-config.js
                thislink += '&turns=' + rrturnsurl;

                thislink += '" target=_blank>route</a>';
                links.push(thislink);
            // display configured url?
            } else if (props.map) {
                links.push('<a href="' + props.map + '" target=_blank>route</a>');
            }

            // turns link
            if (props.fileid) {
                // rrturnsurl is defined in in wp-content/themes/steeps/js/runningroutes directory locally
                // configured runningroutes-config.js
                var thislink = '<a href="' + rrturnsurl + '?title=' + encodeURIComponent(props.name + ' - '
                                + props.distance + ' miles - ' + props.surface)
                                + '&fileid=' + props.fileid;

                if (props.description)
                    thislink += '&descr=' + encodeURIComponent(props.description);
                if (props.gain)
                    thislink += '&gain=' + encodeURIComponent(props.gain);
                // rrrouteurl is defined in in wp-content/themes/steeps/js/runningroutes directory locally
                // configured runningroutes-config.js
                thislink += '&route=' + rrrouteurl;

                thislink += '" target=_blank>turns</a>';
                links.push(thislink);
            }

            // join these all together
            return links.join(separator);
        };

        // some other ancillary functions
        function id(d) {
            return d.geometry.properties.id;
        };

        function dexp(numlocs) {
            var thisdexp = numlocs * (2*rcircle + separation) / (2*pi);
            if (thisdexp < dexpmin) {
                thisdexp = dexpmin;
            } else if (thisdexp > dexpmax) {
                thisdexp = dexpmax;
            }
            // console.log('dexp() numlocs ' + numlocs + ' rcircle ' + rcircle + ' separation ' + separation + ' thisdexp ' + thisdexp);
            return thisdexp;
        };

        function exiting(d) {
            if (rrdebug) console.log('exiting id=' + d.geometry.properties.id)
        };
        function entering(d) {
            if (rrdebug) console.log('entering id=' + d.geometry.properties.id)
        };
        function updating(d) {
            if (rrdebug) console.log('updating id=' + d.geometry.properties.id)
        };
    }
})
