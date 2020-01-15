
function register_group_for_editor(groupname, groupselectselector) {
    // requires Editor
    // expects editor to be set up globally, as in loutilities/table-assets/static/datatables.js
    // call after datatables is initialized
    var staticconfig;

    // editor.on( 'preSubmit', function(e, data, action) {
    editor.on( 'open', function(e, data, action) {
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

// see https://stackoverflow.com/a/18660968/799921
function link_is_external(link_element) {
    return (link_element.host !== window.location.host);
}

// see https://stackoverflow.com/a/5713807/799921
function deparam(query){
  var setValue = function(root, path, value){
    if(path.length > 1){
      var dir = path.shift();
      if( typeof root[dir] == 'undefined' ){
        root[dir] = path[0] == '' ? [] : {};
      }

      arguments.callee(root[dir], path, value);
    }else{
      if( root instanceof Array ){
        root.push(value);
      }else{
        root[path] = value;
      }
    }
  };
  var nvp = query.split('&');
  var data = {};
  for( var i = 0 ; i < nvp.length ; i++ ){
    var pair = nvp[i].split('=');
    var name = decodeURIComponent(pair[0]);
    var value = decodeURIComponent(pair[1]);

    var path = name.match(/(^[^\[]+)(\[.*\]$)?/);
    var first = path[1];
    if(path[2]){
      //case of 'array[level1]' || 'array[level1][level2]'
      path = path[2].match(/(?=\[(.*)\]$)/)[1].split('][')
    }else{
      //case of 'name'
      path = [];
    }
    path.unshift(first);

    setValue(data, path, value);
  }
  return data;
}

function register_group(groupname, groupselectselector, groupargappendselector) {
    var thisgroupappendselector = _.replace( groupargappendselector, '{groupname}', groupname );
    $( thisgroupappendselector ).click( function(e) {
        // don't process external links #71
        if (link_is_external(this)) return;
        e.preventDefault();
        var group = $( groupselectselector ).val();

        var basequery =  $(this).attr('href').split('?');
        var args = {}
        if (basequery.length > 1) {
            args = deparam(basequery[1]);
        }
        args[groupname] = group;
        location.href = $(this).attr('href') + '?' + $.param(args);
    });
}
