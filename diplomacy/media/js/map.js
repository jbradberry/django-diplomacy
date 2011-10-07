function colormap($mapsvg) {
  $.each(diplomacy_map.owns, function(i, v) {
    var id = "#"+v[0];
    var $territory = $mapsvg.find(id);
    $territory.attr('style', "fill: " + diplomacy_map.colors[v[1]]);
  });
}
