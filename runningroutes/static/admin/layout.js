$( function() {
    $( "#navigation ul" ).menu();

    var last_metanav_select_interest = localStorage.getItem('runningroutes_interest');
    var metanav_select_interest = $( "#metanav-select-interest" );
    metanav_select_interest.val(last_metanav_select_interest);
    metanav_select_interest.select2({
      placeholder: 'select an interest',
      theme: "classic",
    });
    metanav_select_interest.on('select2:select', function(e){
      var metanav_new_interest = metanav_select_interest.val();
      localStorage.setItem('runningroutes_interest', metanav_new_interest);

      // translate url rule using interest
      var url_rule = $('#metanav-url-rule').text();
      var last_url = window.location.pathname;
      var new_url = _.replace(decodeURIComponent(url_rule), '<interest>', metanav_new_interest);
      // if new url, reload page
      if (new_url != last_url) {
        window.location.assign(new_url);
      }
      var y = 1;
    });

    // // see https://developers.google.com/identity/sign-in/web/server-side-flow
    // $( '.ui-button' ).button();
    // $( '#signinButton' ).click(function() {
    //     // signInCallback defined below
    //     auth2.grantOfflineAccess().then(signInCallback);
    // });
});

// callback when sign-in button response received
function signInCallback(authResult) {
  if (authResult['code']) {

    // Send the code to the server
    $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/_token',
      // Always include an `X-Requested-With` header in every AJAX request,
      // to protect against CSRF attacks.
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {
        // Handle or verify the server response.
        if (result.authorized) {
            // load directed page
            // this should be window.location.href = result.redirect;
            // but the result.redirect value is giving the wrong URL
            // TODO: fix this, maybe in loutilities.tables
            window.location.href = $SCRIPT_ROOT + '/admin';
        } else {
            // reload to show the error message
            location.reload();
        }
      },
      processData: false,
      data: authResult['code']
    });
  } else {
    // There was an error.
    alert( 'error response received from Google' );
  }
}