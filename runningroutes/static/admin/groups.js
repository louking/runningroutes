// requires Editor
// expects editor to be set up globally, as in loutilities/table-assets/static/datatables.js

function register_group(groupname) {
    var staticconfig;
    editor.on( 'preSubmit', function(e, data, action) {
        // group normally comes from external source
        var group = $( _.replace( '#metanav-select-{groupname}', '{groupname}', groupname )).val();
        // note use of lodash
        staticconfig = _.cloneDeep(editor.ajax());
        var newconfig = _.cloneDeep(staticconfig);
        // substitute group into urls
        for (const action in newconfig) {
            newconfig[action].url = _.replace(decodeURIComponent(newconfig[action].url), _.replace('<{groupname}>', '{groupname}', groupname), group);
        }
        editor.ajax(newconfig);
    })

    editor.on( 'postSubmit', function(e, data, action, xhr) {
        editor.ajax(staticconfig);
    })

}
