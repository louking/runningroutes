  function initMap() {
    var map = new google.maps.Map(document.getElementById('map'), {
      zoom: 10,
      center: google.maps.LatLng(mapcenter[0], mapcenter[1]),
    });

    // add all the markers, keeping track of the bounds
    // see http://stackoverflow.com/questions/1556921/google-map-api-v3-set-bounds-and-center
    var bounds = new google.maps.LatLngBounds();
    for (var i = 0; i < features.length; i++) {
      var coordinates = features[i].geometry.coordinates;
      var properties = features[i].geometry.properties;

      // title is popup text, check iconattrs to see how to format
      if (properties.iconattrs.isAddrShown) {
        var title = properties.name + '\n' + properties.type + '\n' + properties.loctext;

      // if not showAddr just record what it is
      } else {
        var title = properties.iconattrs.icon;
      }

      var position = { lat: parseFloat( coordinates[0] ), lng: parseFloat( coordinates[1] ) };
      if (properties.iconattrs.isShownOnMap) {
        bounds.extend(position)
        var symbol = {
          path: properties.path,
          anchor: new google.maps.Point(properties.anchor[0], properties.anchor[1]),
          fillColor: properties.iconattrs.color,
          strokeColor: properties.iconattrs.color,
          fillOpacity: 1,
          scale: properties.scale,
        };
        var markeropts = {
          position: position,
          title: title,
          map: map,
          icon: symbol,
        };
        var marker = new google.maps.Marker(markeropts);
        map.fitBounds(bounds);
      }
    }
  }

var _domReady = false;
// NOT named _gmapsReady: that name would be a global `var` at script scope, aliasing
// window._gmapsReady (set by the inline onGmapsReady stub in the template) and racing it --
// if gmapsCallback fires (e.g. served from browser cache) before this file finishes loading,
// this file's own `var _gmapsReady = false` would silently stomp the already-true flag back
// to false, and since Google only invokes the callback once, the page hangs forever
var _pageGmapsReady = false;

function _startIconMap() {
  if (!_domReady || !_pageGmapsReady) return;
  initMap();
}

window.onGmapsReady(function() {
  _pageGmapsReady = true;
  _startIconMap();
});

$(function(){
  $('.map-button').button();
  _domReady = true;
  _startIconMap();
  var group = $( '#metanav-select-interest' ).val();
  // locationsurl is defined in frontend_locations.jinja2
  var thislocssurl = _.replace(decodeURIComponent(locationsurl), '<interest>', group);
  $('#table').DataTable({
    // dom: '<"clear">lBfrtip',
    pageLength: -1,
    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
    responsive: {
      details: {
        type: 'none'
      }
    },
    ajax: {
      url: thislocssurl,
      dataSrc: 'features',
    },
    columns: [
      { name: 'name', data: 'geometry.properties.name', responsivePriority: 1 },
      { name: 'type', data: 'geometry.properties.type', responsivePriority: 2 },
      { name: 'subtype', data: 'geometry.properties.subtype', responsivePriority: 1 },
      { name: 'address', data: 'geometry.properties.loctext', responsivePriority: 1 },
      { name: 'notes', data: 'geometry.properties.addl_text', responsivePriority: 1 },
    ]
  });
});