// requires Editor
// expects editor to be set up globally, as in loutilities/table-assets/static/datatables.js

function interest_urltriggers() {
    var staticconfig;
    editor.on( 'preSubmit', function(e, data, action) {
        // interest normally comes from external source
        var interest = 'fsrc';
        // note use of lodash
        staticconfig = _.cloneDeep(editor.ajax());
        var newconfig = _.cloneDeep(staticconfig);
        // substitute interest into urls
        for (const action in newconfig) {
            newconfig[action].url = _.replace(newconfig[action].url, '<interest>', interest);
        }
        editor.ajax(newconfig);
    })

    editor.on( 'postSubmit', function(e, data, action, xhr) {
        editor.ajax(staticconfig);
    })

}
