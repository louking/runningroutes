// render upload filename upon upload complete
// return anonymous function as this gets eval'd at initialization
function renderfileid() {
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

// always register the group to add argument to query params for all links clicked
// from admin pages. Note wait until the page is ready before registering
$(function() {
    register_group('interest', '#metanav-select-interest', 'a' );
});

function check_disable_new() {
    if (_dt_table.data().length >= 1) {
        _dt_table.button( 0 ).disable()
    } else {
        _dt_table.button( 0 ).enable()
    }
};

// this must be done after datatables() is called in datatables.js
// only define afterdatatables if needed
// TODO: there has to be a better way to do this
if ( location.pathname.includes('/iconlocations') ||
     location.pathname.includes('/iconmap') ||
     location.pathname.includes('/icons') ||
     location.pathname.includes('/iconsubtypes')
    ) {
    var openVals;

    function afterdatatables() {
        console.log('afterdatatables()');

        // handle editor substitution before submitting
        register_group_for_editor('interest', '#metanav-select-interest');

        if (location.pathname.includes('/iconmap')) {
            check_disable_new();
            _dt_table.on('draw.dt', function () {
                check_disable_new();
            });
        }
    }
}

if ( location.pathname.includes('/routetable') ) {
    var openVals;

    function afterdatatables() {
        console.log('afterdatatables()');

        // handle editor substitution before submitting
        register_group_for_editor('interest', '#metanav-select-interest' );

        editor.on('uploadXhrSuccess', function (e, fieldName, json) {
            console.log('elev = ' + json.elevation_gain + ' distance = ' + json.distance);
            editor.field('elev').set(json.elevation_gain);
            editor.field('distance').set(json.distance);
            editor.field('active').set(json.active);
            editor.field('location').set(json.start_location);
            editor.field('path_file_id').set(json.path_file_id);
        });

        editor.on('initCreate', function () {
            editor.set('active', 1)
            editor.field('active').hide()
        });

        editor.on('initEdit', function () {
            editor.field('active').show()
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
};