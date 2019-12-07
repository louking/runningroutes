// render upload filename upon upload complete
// return anonymous function as this gets eval'd at initialization
function rendergpxfile() {
    return function(fileid) {
        var renderfile = fileid ? editor.file('data', fileid).filename : '';
        return renderfile;
    }
}

// render active field
function renderactive() {
    return function(val) {
        var value = (val==1) ? 'active' : 'deleted'
        return value
    }
}

// this must be done after datatables() is called in datatables.js
var openVals;
function afterdatatables(){
    console.log('afterdatatables()');

    editor.on( 'uploadXhrSuccess', function ( e, fieldName, json ) {
        console.log ('elev = ' + json.elev + ' distance = ' + json.distance);
        editor.field('elev').set(json.elev);
        editor.field('distance').set(json.distance);
        editor.field('active').set(json.active);
        editor.field('location').set(json.location);
    } );

    editor.on('initCreate', function() {
        editor.set('active', 1)
        editor.field('active').hide()
    });

    editor.on('initEdit', function() {
        var fileid = editor.get('fileid');
        editor.set('turns', 'Loading...')
        editor.field('active').show()
        $.ajax({
            // rr_turns_url_prefix comes from runningroute-*-config.js
            url: rr_turns_url_prefix + '/admin/' + fileid + '/turns', 
            success : function(data) {
                editor.set('turns', data.turns)
            },
            error : function(jqXHR, textStatus, errorThrown) {
                editor.set('turns', 'ERROR: could not retrieve turn data\n'
                            + '   ' + errorThrown)
            },
        });
        
    });

    // confirm before closing window for unsaved changes
    // from https://datatables.net/forums/discussion/32883
    // but see https://datatables.net/forums/discussion/46526/confirmation-on-form-close
    
    // editor
    //   .on("open", function() {
    //     console.log('editor on open fired');
    //     // Store the values of the fields on open
    //     openVals = JSON.stringify(editor.get());
     
    //     editor.on("preClose", function(e) {
    //       console.log('editor on preClose fired');
    //       // On close, check if the values have changed and ask for closing confirmation if they have
    //       if (openVals !== JSON.stringify(editor.get())) {
    //         return confirm(
    //           "You have unsaved changes. Are you sure you want to exit?"
    //         );
    //       }
    //     });
    //   })
    //   .on("submit", function() {
    //     console.log('editor on submit fired')
    //     editor.off("preClose");
    //   });
};