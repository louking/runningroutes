
function register_group_for_editor(groupname, groupselectselector) {
    // requires Editor
    // expects editor to be set up globally, as in loutilities/table-assets/static/datatables.js
    // call after datatables is initialized
    var staticconfig;

    editor.on( 'preSubmit', function(e, data, action) {
        // group comes from external source
        var group = $( groupselectselector ).val();
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

function register_group(groupname, groupselectselector, groupargappendselector) {
    var thisgroupappendselector = _.replace( groupargappendselector, '{groupname}', groupname );
    $( thisgroupappendselector ).click( function(e) {
        e.preventDefault();
        var group = $( groupselectselector ).val();
        var args = {};
        args[groupname] = group;
        // TODO: should really check if there are already args here first
        location.href = $(this).attr('href') + '?' + $.param(args);
    });
}
