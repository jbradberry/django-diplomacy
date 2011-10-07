function colormap($mapsvg) {
  $.each(diplomacy_map.owns, function(i, v) {
    var id = "#"+v[0];
    var $territory = $mapsvg.find(id);
    $territory.attr('style', "fill: " + diplomacy_map.colors[v[1]]);
  });
}

function tokenizemap($mapsvg) {
  var $tokens = $($mapsvg.find("#layer5")[0]);
  var $army = $($mapsvg.find("#army_prototype")[0]);
  var $fleet = $($mapsvg.find("#fleet_prototype")[0]);
  $.each(diplomacy_map.units, function(i, v) {
    console.log(v);
    if ( v[1] === 'A' ) { var $unit = $army.clone(); }
    else { var $unit = $fleet.clone(); }

    var style = "color:#000000;fill:" + diplomacy_map.colors[v[2]] + ";stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;opacity:1";
    $unit.attr({'id': v[1] + i, 'style': style,
		'x': diplomacy_map.coordinates[v[0]][0],
		'y': diplomacy_map.coordinates[v[0]][1]});
    $tokens.append($unit);
  });
}
