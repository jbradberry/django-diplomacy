function colormap(map) {
  var mapsvg = map.getSVGDocument();
  $.each(state, function(i, v) {
    var id = "#"+v[0];
    var territory = $(mapsvg).find(id)[0];
    territory.style.setProperty("fill", colors[v[1]], "");
  });
}
