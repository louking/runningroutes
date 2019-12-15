// requires Editor
// expects editor to be set up globally, as in loutilities/table-assets/static/datatables.js

function register_group(groupname) {
    var staticconfig;
    editor.on( 'preSubmit', function(e, data, action) {
        // interest normally comes from external source
        var interest = $( _.replace( '#metanav-select-{groupname}', '{groupname}', groupname )).val();
        // note use of lodash
        staticconfig = _.cloneDeep(editor.ajax());
        var newconfig = _.cloneDeep(staticconfig);
        // substitute interest into urls
        for (const action in newconfig) {
            newconfig[action].url = _.replace(decodeURIComponent(newconfig[action].url), _.replace('<{groupname}>', '{groupname}', groupname), interest);
        }
        editor.ajax(newconfig);
    })

    editor.on( 'postSubmit', function(e, data, action, xhr) {
        editor.ajax(staticconfig);
    })

}
