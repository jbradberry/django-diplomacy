var coordinates = {
  "Adriatic Sea": ['442', '593'],
  "Aegean Sea": ['594', '713'],
  "Baltic Sea": ['473', '337'],
  "Barents Sea": ['634', '12'],
  "Black Sea": ['712', '566'],
  "Eastern Mediterranean": ['677', '742'],
  "English Channel": ['219', '409'],
  "Gulf of Bothnia": ['521', '267'],
  "Gulf of Lyon": ['271', '608'],
  "Helgoland Bight": ['370', '350'],
  "Ionian Sea": ['475', '726'],
  "Irish Sea": ['165', '373'],
  "Mid-Atlantic Ocean": ['35', '462'],
  "North Atlantic Ocean": ['75', '152'],
  "North Sea": ['315', '289'],
  "Norwegian Sea": ['338', '72'],
  "Skagerrak": ['414', '278'],
  "Tyrrhenian Sea": ['392', '650'],
  "Western Mediterranean": ['243', '667'],
  "Ankara": ['748', '614'],
  "Albania": ['525', '634'],
  "Apulia": ['461', '620'],
  "Armenia": ['861', '621'],
  "Berlin": ['438', '379'],
  "Belgium": ['314', '409'],
  "Bohemia": ['450', '446'],
  "Brest": ['231', '446'],
  "Budapest": ['540', '500'],
  "Bulgaria": ['599', '593'],
  "Bulgaria (SC)": ['600', '633'],
  "Bulgaria (EC)": ['638', '589'],
  "Burgundy": ['314', '474'],
  "Clyde": ['240', '259'],
  "Constantinople": ['656', '637'],
  "Denmark": ['410', '316'],
  "Edinburgh": ['275', '262'],
  "Finland": ['575', '175'],
  "Galicia": ['555', '450'],
  "Gascony": ['241', '517'],
  "Greece": ['557', '651'],
  "Holland": ['335', '382'],
  "Kiel": ['387', '386'],
  "Liverpool": ['252', '321'],
  "Livonia": ['569', '316'],
  "London": ['277', '375'],
  "Marseilles": ['293', '547'],
  "Moscow": ['770', '285'],
  "Munich": ['389', '458'],
  "Naples": ['457', '658'],
  "North Africa": ['164', '716'],
  "Norway": ['412', '193'],
  "Paris": ['274', '459'],
  "Picardy": ['288', '426'],
  "Piedmont": ['360', '535'],
  "Portugal": ['85', '558'],
  "Prussia": ['504', '359'],
  "Rome": ['411', '612'],
  "Ruhr": ['359', '424'],
  "Rumania": ['622', '537'],
  "Serbia": ['535', '580'],
  "Sevastopol": ['770', '430'],
  "Silesia": ['471', '413'],
  "Smyrna": ['712', '680'],
  "Spain": ['154', '607'],
  "Spain (NC)": ['148', '515'],
  "Spain (SC)": ['192', '634'],
  "St. Petersburg": ['758', '124'],
  "St. Petersburg (NC)": ['680', '63'],
  "St. Petersburg (SC)": ['587', '249'],
  "Sweden": ['480', '185'],
  "Syria": ['832', '693'],
  "Trieste": ['470', '551'],
  "Tunisia": ['351', '733'],
  "Tuscany": ['395', '577'],
  "Tyrolia": ['413', '500'],
  "Ukraine": ['631', '423'],
  "Venice": ['406', '548'],
  "Vienna": ['486', '476'],
  "Wales": ['222', '363'],
  "Warsaw": ['552', '403'],
  "Yorkshire": ['278', '332']
};

function updatemap($mapsvg) {
  colormap($mapsvg);
  tokenizemap($mapsvg);
}

function colormap($mapsvg) {
  $.each(map_config.owns, function(i, v) {
    var id = "#"+v[0];
    var $territory = $mapsvg.find(id);
    $territory.attr('style', "fill: " + map_config.colors[v[1]]);
  });
}

function tokenizemap($mapsvg) {
  var $tokens = $($mapsvg.find("#prototypes")[0]);
  var $army = $($mapsvg.find("#army_prototype")[0]);
  var $fleet = $($mapsvg.find("#fleet_prototype")[0]);
  $.each(map_config.units, function(i, v) {
    var $unit;
    if ( v[1] === 'A' ) { $unit = $army.clone(); }
    else { $unit = $fleet.clone(); }

    var style = "color:#000000;fill:" + map_config.colors[v[2]] + ";stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;stroke-dashoffset:0;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;opacity:1";
    $unit.attr({'id': v[1] + i, 'style': style,
                'x': coordinates[v[0]][0],
                'y': coordinates[v[0]][1],
                'title': v[1] + " " + v[0]
               });
    $unit.find("title").text(v[1]+" "+v[0]);
    $tokens.append($unit);
  });
}

function update() {
  var $mapobj = $("#map");
  var $map = $($mapobj[0].getSVGDocument());
  updatemap($map);
}

$(window).load(function() {
  setTimeout(update, 50); // give Chrome a chance to grab the SVG
});
