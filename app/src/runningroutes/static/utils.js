// get arguments -- https://stackoverflow.com/questions/19491336/get-url-parameter-jquery-or-how-to-get-query-string-values-in-js
if (jQuery) {
  function urlParam(name) {
      var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
      if (results==null){
         return null;
      }
      else{
         return decodeURIComponent(results[1]) || 0;
      }
  }

  // Serialize an array of form elements or a set of
  // key/values into a query string
  // adapted from jQuery.param
  function setParams(a) {
    var prefix,
      s = [],
      add = function( key, valueOrFunction ) {

        // If value is a function, invoke it and use its return value
        var value = typeof obj === "function" && typeof obj.nodeType !== "number" ?
          valueOrFunction() :
          valueOrFunction;

        s[ s.length ] = encodeURIComponent( key ) + "=" +
          encodeURIComponent( value == null ? "" : value );
      };

      // encode each item
      for ( prefix in a ) {
        add( prefix, a[ prefix ] );
      }

    // Return the resulting serialization
    return s.join( "&" );
  };
}

// degrees to Radians
function toRad(x) {
  return x * Math.PI / 180;
}

// compute haversine distance with elevation accounted for
// https://stackoverflow.com/questions/14560999/using-the-haversine-formula-in-javascript
// https://math.stackexchange.com/questions/2075092/haversine-formula-that-includes-an-altitude-parameter
function haversineDistance(coords1, coords2, isMiles) {
  var lat1 = coords1[0];
  var lon1 = coords1[1];
  var ele1 = coords1[2];  // units feet or meters

  var lat2 = coords2[0];
  var lon2 = coords2[1];
  var ele2 = coords2[2];

  var R = 6371; // km

  var x1 = lat2 - lat1;
  var dLat = toRad(x1);
  var x2 = lon2 - lon1;
  var dLon = toRad(x2)
  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  var d = R * c;

  if(isMiles) d /= 1.609344;

  // account for elevation. ok if difference is negative because squaring
  if (isMiles) {
    ele1 /= 5280;
    ele2 /= 5280;
  } else {
    ele1 /= 1000;
    ele2 /= 1000;
  }
  var de = ele2 - ele1;
  d = Math.sqrt(d*d + de*de);

  return d;
}

// cookie handling
// https://www.w3schools.com/js/js_cookies.asp
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
