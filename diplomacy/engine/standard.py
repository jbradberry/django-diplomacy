
# For every territory, specify:
#   - the initial owning empire, or None
#   - whether the territory is a supply center
#   - the subname (in standard, the coast name or an empty string)
#       and subregion type (land or sea) of the initial unit, or None
definition = {
    'Adriatic Sea': (None, False, None),
    'Aegean Sea': (None, False, None),
    'Albania': (None, False, None),
    'Ankara': ('Turkey', True, ('', 'S')),
    'Apulia': ('Italy', False, None),
    'Armenia': ('Turkey', False, None),
    'Baltic Sea': (None, False, None),
    'Barents Sea': (None, False, None),
    'Belgium': (None, True, None),
    'Berlin': ('Germany', True, ('', 'L')),
    'Black Sea': (None, False, None),
    'Bohemia': ('Austria-Hungary', False, None),
    'Brest': ('France', True, ('', 'S')),
    'Budapest': ('Austria-Hungary', True, ('', 'L')),
    'Bulgaria': (None, True, None),
    'Burgundy': ('France', False, None),
    'Clyde': ('England', False, None),
    'Constantinople': ('Turkey', True, ('', 'L')),
    'Denmark': (None, True, None),
    'Eastern Mediterranean': (None, False, None),
    'Edinburgh': ('England', True, ('', 'S')),
    'English Channel': (None, False, None),
    'Finland': ('Russia', False, None),
    'Galicia': ('Austria-Hungary', False, None),
    'Gascony': ('France', False, None),
    'Greece': (None, True, None),
    'Gulf of Bothnia': (None, False, None),
    'Gulf of Lyon': (None, False, None),
    'Helgoland Bight': (None, False, None),
    'Holland': (None, True, None),
    'Ionian Sea': (None, False, None),
    'Irish Sea': (None, False, None),
    'Kiel': ('Germany', True, ('', 'S')),
    'Liverpool': ('England', True, ('', 'L')),
    'Livonia': ('Russia', False, None),
    'London': ('England', True, ('', 'S')),
    'Marseilles': ('France', True, ('', 'L')),
    'Mid-Atlantic Ocean': (None, False, None),
    'Moscow': ('Russia', True, ('', 'L')),
    'Munich': ('Germany', True, ('', 'L')),
    'Naples': ('Italy', True, ('', 'S')),
    'North Africa': (None, False, None),
    'North Atlantic Ocean': (None, False, None),
    'North Sea': (None, False, None),
    'Norway': (None, True, None),
    'Norwegian Sea': (None, False, None),
    'Paris': ('France', True, ('', 'L')),
    'Picardy': ('France', False, None),
    'Piedmont': ('Italy', False, None),
    'Portugal': (None, True, None),
    'Prussia': ('Germany', False, None),
    'Rome': ('Italy', True, ('', 'L')),
    'Ruhr': ('Germany', False, None),
    'Rumania': (None, True, None),
    'Serbia': (None, True, None),
    'Sevastopol': ('Russia', True, ('', 'S')),
    'Silesia': ('Germany', False, None),
    'Skagerrak': (None, False, None),
    'Smyrna': ('Turkey', True, ('', 'L')),
    'Spain': (None, True, None),
    'St. Petersburg': ('Russia', True, ('SC', 'S')),
    'Sweden': (None, True, None),
    'Syria': ('Turkey', False, None),
    'Trieste': ('Austria-Hungary', True, ('', 'S')),
    'Tunisia': (None, True, None),
    'Tuscany': ('Italy', False, None),
    'Tyrolia': ('Austria-Hungary', False, None),
    'Tyrrhenian Sea': (None, False, None),
    'Ukraine': ('Russia', False, None),
    'Venice': ('Italy', True, ('', 'L')),
    'Vienna': ('Austria-Hungary', True, ('', 'L')),
    'Wales': ('England', False, None),
    'Warsaw': ('Russia', True, ('', 'L')),
    'Western Mediterranean': (None, False, None),
    'Yorkshire': ('England', False, None),
}

# Mapping of the canonical name for each territory to the allowable
# variants, without fuzzing.
names = {
    'Adriatic Sea': (
        'Adriatic Sea',
        'Adr',
    ),
    'Aegean Sea': (
        'Aegean Sea',
        'Aeg',
    ),
    'Albania': (
        'Albania',
        'Alb',
    ),
    'Ankara': (
        'Ankara',
        'Ank',
    ),
    'Apulia': (
        'Apulia',
        'Apu',
    ),
    'Armenia': (
        'Armenia',
        'Arm',
    ),
    'Baltic Sea': (
        'Baltic Sea',
        'Bal',
    ),
    'Barents Sea': (
        'Barents Sea',
        'Bar',
    ),
    'Belgium': (
        'Belgium',
        'Bel',
    ),
    'Berlin': (
        'Berlin',
        'Ber',
    ),
    'Black Sea': (
        'Black Sea',
        'Bla',
    ),
    'Bohemia': (
        'Bohemia',
        'Boh',
    ),
    'Brest': (
        'Brest',
        'Bre',
    ),
    'Budapest': (
        'Budapest',
        'Bud',
    ),
    'Bulgaria': (
        'Bulgaria',
        'Bul',
    ),
    'Burgundy': (
        'Burgundy',
        'Bur',
    ),
    'Clyde': (
        'Clyde',
        'Cly',
    ),
    'Constantinople': (
        'Constantinople',
        'Con',
    ),
    'Denmark': (
        'Denmark',
        'Den',
    ),
    'Eastern Mediterranean': (
        'Eastern Mediterranean',
        'Eas',
    ),
    'Edinburgh': (
        'Edinburgh',
        'Edi',
    ),
    'English Channel': (
        'English Channel',
        'Eng',
    ),
    'Finland': (
        'Finland',
        'Fin',
    ),
    'Galicia': (
        'Galicia',
        'Gal',
    ),
    'Gascony': (
        'Gascony',
        'Gas',
    ),
    'Greece': (
        'Greece',
        'Gre',
    ),
    'Gulf of Bothnia': (
        'Gulf of Bothnia',
        'Bot',
    ),
    'Gulf of Lyon': (
        'Gulf of Lyon',
        'GoL',
    ),
    'Helgoland Bight': (
        'Helgoland Bight',
        'Hel',
    ),
    'Holland': (
        'Holland',
        'Hol',
    ),
    'Ionian Sea': (
        'Ionian Sea',
        'Ion',
    ),
    'Irish Sea': (
        'Irish Sea',
        'Iri',
    ),
    'Kiel': (
        'Kiel',
        'Kie',
    ),
    'Liverpool': (
        'Liverpool',
        'Lvp',
    ),
    'Livonia': (
        'Livonia',
        'Lvn',
    ),
    'London': (
        'London',
        'Lon',
    ),
    'Marseilles': (
        'Marseilles',
        'Mar',
    ),
    'Mid-Atlantic Ocean': (
        'Mid-Atlantic Ocean',
        'Mid',
    ),
    'Moscow': (
        'Moscow',
        'Mos',
    ),
    'Munich': (
        'Munich',
        'Mun',
    ),
    'Naples': (
        'Naples',
        'Nap',
    ),
    'North Africa': (
        'North Africa',
        'NAf',
    ),
    'North Atlantic Ocean': (
        'North Atlantic Ocean',
        'NAt',
    ),
    'North Sea': (
        'North Sea',
        'Nth',
    ),
    'Norway': (
        'Norway',
        'Nwy',
    ),
    'Norwegian Sea': (
        'Norwegian Sea',
        'Nrg',
    ),
    'Paris': (
        'Paris',
        'Par',
    ),
    'Picardy': (
        'Picardy',
        'Pic',
    ),
    'Piedmont': (
        'Piedmont',
        'Pie',
    ),
    'Portugal': (
        'Portugal',
        'Por',
    ),
    'Prussia': (
        'Prussia',
        'Pru',
    ),
    'Rome': (
        'Rome',
        'Rom',
    ),
    'Ruhr': (
        'Ruhr',
        'Ruh',
    ),
    'Rumania': (
        'Rumania',
        'Rum',
    ),
    'Serbia': (
        'Serbia',
        'Ser',
    ),
    'Sevastopol': (
        'Sevastopol',
        'Sev',
    ),
    'Silesia': (
        'Silesia',
        'Sil',
    ),
    'Skagerrak': (
        'Skagerrak',
        'Ska',
    ),
    'Smyrna': (
        'Smyrna',
        'Smy',
    ),
    'Spain': (
        'Spain',
        'Spa',
    ),
    'St. Petersburg': (
        'St. Petersburg',
        'StP',
    ),
    'Sweden': (
        'Sweden',
        'Swe',
    ),
    'Syria': (
        'Syria',
        'Syr',
    ),
    'Trieste': (
        'Trieste',
        'Tri',
    ),
    'Tunisia': (
        'Tunisia',
        'Tunis',
        'Tun',
    ),
    'Tuscany': (
        'Tuscany',
        'Tus',
    ),
    'Tyrolia': (
        'Tyrolia',
        'Tyr',
    ),
    'Tyrrhenian Sea': (
        'Tyrrhenian Sea',
        'Tyn',
    ),
    'Ukraine': (
        'Ukraine',
        'Ukr',
    ),
    'Venice': (
        'Venice',
        'Ven',
    ),
    'Vienna': (
        'Vienna',
        'Vie',
    ),
    'Wales': (
        'Wales',
        'Wal',
    ),
    'Warsaw': (
        'Warsaw',
        'War',
    ),
    'Western Mediterranean': (
        'Western Mediterranean',
        'Wes',
    ),
    'Yorkshire': (
        'Yorkshire',
        'Yor',
    ),
}

# Provide a case-insensitve lookup of user-provided names or
# abbreviations to the canonical form.
name_lookup = {
    abbrev.lower(): n for n, abbrevs in names.items() for abbrev in abbrevs
}

# Define the connectivity of the map.
#   (name, subname or empty string, land or sea)
mapping = {
    ('Adriatic Sea', '', 'S'): (
        ('Albania', '', 'S'),
        ('Apulia', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Trieste', '', 'S'),
        ('Venice', '', 'S'),
    ),
    ('Aegean Sea', '', 'S'): (
        ('Bulgaria', 'SC', 'S'),
        ('Constantinople', '', 'S'),
        ('Eastern Mediterranean', '', 'S'),
        ('Greece', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Smyrna', '', 'S'),
    ),
    ('Albania', '', 'L'): (
        ('Greece', '', 'L'),
        ('Serbia', '', 'L'),
        ('Trieste', '', 'L'),
    ),
    ('Albania', '', 'S'): (
        ('Adriatic Sea', '', 'S'),
        ('Greece', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Trieste', '', 'S'),
    ),
    ('Ankara', '', 'L'): (
        ('Armenia', '', 'L'),
        ('Constantinople', '', 'L'),
        ('Smyrna', '', 'L'),
    ),
    ('Ankara', '', 'S'): (
        ('Armenia', '', 'S'),
        ('Black Sea', '', 'S'),
        ('Constantinople', '', 'S'),
    ),
    ('Apulia', '', 'L'): (
        ('Naples', '', 'L'),
        ('Rome', '', 'L'),
        ('Venice', '', 'L'),
    ),
    ('Apulia', '', 'S'): (
        ('Adriatic Sea', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Naples', '', 'S'),
        ('Venice', '', 'S'),
    ),
    ('Armenia', '', 'L'): (
        ('Ankara', '', 'L'),
        ('Sevastopol', '', 'L'),
        ('Smyrna', '', 'L'),
        ('Syria', '', 'L'),
    ),
    ('Armenia', '', 'S'): (
        ('Ankara', '', 'S'),
        ('Black Sea', '', 'S'),
        ('Sevastopol', '', 'S'),
    ),
    ('Baltic Sea', '', 'S'): (
        ('Berlin', '', 'S'),
        ('Denmark', '', 'S'),
        ('Gulf of Bothnia', '', 'S'),
        ('Kiel', '', 'S'),
        ('Livonia', '', 'S'),
        ('Prussia', '', 'S'),
        ('Sweden', '', 'S'),
    ),
    ('Barents Sea', '', 'S'): (
        ('Norway', '', 'S'),
        ('Norwegian Sea', '', 'S'),
        ('St. Petersburg', 'NC', 'S'),
    ),
    ('Belgium', '', 'L'): (
        ('Burgundy', '', 'L'),
        ('Holland', '', 'L'),
        ('Picardy', '', 'L'),
        ('Ruhr', '', 'L'),
    ),
    ('Belgium', '', 'S'): (
        ('English Channel', '', 'S'),
        ('Holland', '', 'S'),
        ('North Sea', '', 'S'),
        ('Picardy', '', 'S'),
    ),
    ('Berlin', '', 'L'): (
        ('Kiel', '', 'L'),
        ('Munich', '', 'L'),
        ('Prussia', '', 'L'),
        ('Silesia', '', 'L'),
    ),
    ('Berlin', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Kiel', '', 'S'),
        ('Prussia', '', 'S'),
    ),
    ('Black Sea', '', 'S'): (
        ('Ankara', '', 'S'),
        ('Armenia', '', 'S'),
        ('Bulgaria', 'EC', 'S'),
        ('Constantinople', '', 'S'),
        ('Rumania', '', 'S'),
        ('Sevastopol', '', 'S'),
    ),
    ('Bohemia', '', 'L'): (
        ('Galicia', '', 'L'),
        ('Munich', '', 'L'),
        ('Silesia', '', 'L'),
        ('Tyrolia', '', 'L'),
        ('Vienna', '', 'L'),
    ),
    ('Brest', '', 'L'): (
        ('Gascony', '', 'L'),
        ('Paris', '', 'L'),
        ('Picardy', '', 'L'),
    ),
    ('Brest', '', 'S'): (
        ('English Channel', '', 'S'),
        ('Gascony', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Picardy', '', 'S'),
    ),
    ('Budapest', '', 'L'): (
        ('Galicia', '', 'L'),
        ('Rumania', '', 'L'),
        ('Serbia', '', 'L'),
        ('Trieste', '', 'L'),
        ('Vienna', '', 'L'),
    ),
    ('Bulgaria', '', 'L'): (
        ('Constantinople', '', 'L'),
        ('Greece', '', 'L'),
        ('Rumania', '', 'L'),
        ('Serbia', '', 'L'),
    ),
    ('Bulgaria', 'EC', 'S'): (
        ('Black Sea', '', 'S'),
        ('Constantinople', '', 'S'),
        ('Rumania', '', 'S'),
    ),
    ('Bulgaria', 'SC', 'S'): (
        ('Aegean Sea', '', 'S'),
        ('Constantinople', '', 'S'),
        ('Greece', '', 'S'),
    ),
    ('Burgundy', '', 'L'): (
        ('Belgium', '', 'L'),
        ('Gascony', '', 'L'),
        ('Marseilles', '', 'L'),
        ('Munich', '', 'L'),
        ('Paris', '', 'L'),
        ('Picardy', '', 'L'),
        ('Ruhr', '', 'L'),
    ),
    ('Clyde', '', 'L'): (
        ('Edinburgh', '', 'L'),
        ('Liverpool', '', 'L'),
    ),
    ('Clyde', '', 'S'): (
        ('Edinburgh', '', 'S'),
        ('Liverpool', '', 'S'),
        ('North Atlantic Ocean', '', 'S'),
        ('Norwegian Sea', '', 'S'),
    ),
    ('Constantinople', '', 'L'): (
        ('Ankara', '', 'L'),
        ('Bulgaria', '', 'L'),
        ('Smyrna', '', 'L'),
    ),
    ('Constantinople', '', 'S'): (
        ('Aegean Sea', '', 'S'),
        ('Ankara', '', 'S'),
        ('Black Sea', '', 'S'),
        ('Bulgaria', 'EC', 'S'),
        ('Bulgaria', 'SC', 'S'),
        ('Smyrna', '', 'S'),
    ),
    ('Denmark', '', 'L'): (
        ('Kiel', '', 'L'),
        ('Sweden', '', 'L'),
    ),
    ('Denmark', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Helgoland Bight', '', 'S'),
        ('Kiel', '', 'S'),
        ('North Sea', '', 'S'),
        ('Skagerrak', '', 'S'),
        ('Sweden', '', 'S'),
    ),
    ('Eastern Mediterranean', '', 'S'): (
        ('Aegean Sea', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Smyrna', '', 'S'),
        ('Syria', '', 'S'),
    ),
    ('Edinburgh', '', 'L'): (
        ('Clyde', '', 'L'),
        ('Liverpool', '', 'L'),
        ('Yorkshire', '', 'L'),
    ),
    ('Edinburgh', '', 'S'): (
        ('Clyde', '', 'S'),
        ('North Sea', '', 'S'),
        ('Norwegian Sea', '', 'S'),
        ('Yorkshire', '', 'S'),
    ),
    ('English Channel', '', 'S'): (
        ('Belgium', '', 'S'),
        ('Brest', '', 'S'),
        ('Irish Sea', '', 'S'),
        ('London', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('North Sea', '', 'S'),
        ('Picardy', '', 'S'),
        ('Wales', '', 'S'),
    ),
    ('Finland', '', 'L'): (
        ('Norway', '', 'L'),
        ('St. Petersburg', '', 'L'),
        ('Sweden', '', 'L'),
    ),
    ('Finland', '', 'S'): (
        ('Gulf of Bothnia', '', 'S'),
        ('St. Petersburg', 'SC', 'S'),
        ('Sweden', '', 'S'),
    ),
    ('Galicia', '', 'L'): (
        ('Bohemia', '', 'L'),
        ('Budapest', '', 'L'),
        ('Rumania', '', 'L'),
        ('Silesia', '', 'L'),
        ('Ukraine', '', 'L'),
        ('Vienna', '', 'L'),
        ('Warsaw', '', 'L'),
    ),
    ('Gascony', '', 'L'): (
        ('Brest', '', 'L'),
        ('Burgundy', '', 'L'),
        ('Marseilles', '', 'L'),
        ('Paris', '', 'L'),
        ('Spain', '', 'L'),
    ),
    ('Gascony', '', 'S'): (
        ('Brest', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Spain', 'NC', 'S'),
    ),
    ('Greece', '', 'L'): (
        ('Albania', '', 'L'),
        ('Bulgaria', '', 'L'),
        ('Serbia', '', 'L'),
    ),
    ('Greece', '', 'S'): (
        ('Aegean Sea', '', 'S'),
        ('Albania', '', 'S'),
        ('Bulgaria', 'SC', 'S'),
        ('Ionian Sea', '', 'S'),
    ),
    ('Gulf of Bothnia', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Finland', '', 'S'),
        ('Livonia', '', 'S'),
        ('St. Petersburg', 'SC', 'S'),
        ('Sweden', '', 'S'),
    ),
    ('Gulf of Lyon', '', 'S'): (
        ('Marseilles', '', 'S'),
        ('Piedmont', '', 'S'),
        ('Spain', 'SC', 'S'),
        ('Tuscany', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
        ('Western Mediterranean', '', 'S'),
    ),
    ('Helgoland Bight', '', 'S'): (
        ('Denmark', '', 'S'),
        ('Holland', '', 'S'),
        ('Kiel', '', 'S'),
        ('North Sea', '', 'S'),
    ),
    ('Holland', '', 'L'): (
        ('Belgium', '', 'L'),
        ('Kiel', '', 'L'),
        ('Ruhr', '', 'L'),
    ),
    ('Holland', '', 'S'): (
        ('Belgium', '', 'S'),
        ('Helgoland Bight', '', 'S'),
        ('Kiel', '', 'S'),
        ('North Sea', '', 'S'),
    ),
    ('Ionian Sea', '', 'S'): (
        ('Adriatic Sea', '', 'S'),
        ('Aegean Sea', '', 'S'),
        ('Albania', '', 'S'),
        ('Apulia', '', 'S'),
        ('Eastern Mediterranean', '', 'S'),
        ('Greece', '', 'S'),
        ('Naples', '', 'S'),
        ('Tunisia', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
    ),
    ('Irish Sea', '', 'S'): (
        ('English Channel', '', 'S'),
        ('Liverpool', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('North Atlantic Ocean', '', 'S'),
        ('Wales', '', 'S'),
    ),
    ('Kiel', '', 'L'): (
        ('Berlin', '', 'L'),
        ('Denmark', '', 'L'),
        ('Holland', '', 'L'),
        ('Munich', '', 'L'),
        ('Ruhr', '', 'L'),
    ),
    ('Kiel', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Berlin', '', 'S'),
        ('Denmark', '', 'S'),
        ('Helgoland Bight', '', 'S'),
        ('Holland', '', 'S'),
    ),
    ('Liverpool', '', 'L'): (
        ('Clyde', '', 'L'),
        ('Edinburgh', '', 'L'),
        ('Wales', '', 'L'),
        ('Yorkshire', '', 'L'),
    ),
    ('Liverpool', '', 'S'): (
        ('Clyde', '', 'S'),
        ('Irish Sea', '', 'S'),
        ('North Atlantic Ocean', '', 'S'),
        ('Wales', '', 'S'),
    ),
    ('Livonia', '', 'L'): (
        ('Moscow', '', 'L'),
        ('Prussia', '', 'L'),
        ('St. Petersburg', '', 'L'),
        ('Warsaw', '', 'L'),
    ),
    ('Livonia', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Gulf of Bothnia', '', 'S'),
        ('Prussia', '', 'S'),
        ('St. Petersburg', 'SC', 'S'),
    ),
    ('London', '', 'L'): (
        ('Wales', '', 'L'),
        ('Yorkshire', '', 'L'),
    ),
    ('London', '', 'S'): (
        ('English Channel', '', 'S'),
        ('North Sea', '', 'S'),
        ('Wales', '', 'S'),
        ('Yorkshire', '', 'S'),
    ),
    ('Marseilles', '', 'L'): (
        ('Burgundy', '', 'L'),
        ('Gascony', '', 'L'),
        ('Piedmont', '', 'L'),
        ('Spain', '', 'L'),
    ),
    ('Marseilles', '', 'S'): (
        ('Gulf of Lyon', '', 'S'),
        ('Piedmont', '', 'S'),
        ('Spain', 'SC', 'S'),
    ),
    ('Mid-Atlantic Ocean', '', 'S'): (
        ('Brest', '', 'S'),
        ('English Channel', '', 'S'),
        ('Gascony', '', 'S'),
        ('Irish Sea', '', 'S'),
        ('North Africa', '', 'S'),
        ('North Atlantic Ocean', '', 'S'),
        ('Portugal', '', 'S'),
        ('Spain', 'NC', 'S'),
        ('Spain', 'SC', 'S'),
        ('Western Mediterranean', '', 'S'),
    ),
    ('Moscow', '', 'L'): (
        ('Livonia', '', 'L'),
        ('Sevastopol', '', 'L'),
        ('St. Petersburg', '', 'L'),
        ('Ukraine', '', 'L'),
        ('Warsaw', '', 'L'),
    ),
    ('Munich', '', 'L'): (
        ('Berlin', '', 'L'),
        ('Bohemia', '', 'L'),
        ('Burgundy', '', 'L'),
        ('Kiel', '', 'L'),
        ('Ruhr', '', 'L'),
        ('Silesia', '', 'L'),
        ('Tyrolia', '', 'L'),
    ),
    ('Naples', '', 'L'): (
        ('Apulia', '', 'L'),
        ('Rome', '', 'L'),
    ),
    ('Naples', '', 'S'): (
        ('Apulia', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Rome', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
    ),
    ('North Africa', '', 'L'): (
        ('Tunisia', '', 'L'),
    ),
    ('North Africa', '', 'S'): (
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Tunisia', '', 'S'),
        ('Western Mediterranean', '', 'S'),
    ),
    ('North Atlantic Ocean', '', 'S'): (
        ('Clyde', '', 'S'),
        ('Irish Sea', '', 'S'),
        ('Liverpool', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Norwegian Sea', '', 'S'),
    ),
    ('North Sea', '', 'S'): (
        ('Belgium', '', 'S'),
        ('Denmark', '', 'S'),
        ('Edinburgh', '', 'S'),
        ('English Channel', '', 'S'),
        ('Helgoland Bight', '', 'S'),
        ('Holland', '', 'S'),
        ('London', '', 'S'),
        ('Norway', '', 'S'),
        ('Norwegian Sea', '', 'S'),
        ('Skagerrak', '', 'S'),
        ('Yorkshire', '', 'S'),
    ),
    ('Norway', '', 'L'): (
        ('Finland', '', 'L'),
        ('St. Petersburg', '', 'L'),
        ('Sweden', '', 'L'),
    ),
    ('Norway', '', 'S'): (
        ('Barents Sea', '', 'S'),
        ('North Sea', '', 'S'),
        ('Norwegian Sea', '', 'S'),
        ('Skagerrak', '', 'S'),
        ('St. Petersburg', 'NC', 'S'),
        ('Sweden', '', 'S'),
    ),
    ('Norwegian Sea', '', 'S'): (
        ('Barents Sea', '', 'S'),
        ('Clyde', '', 'S'),
        ('Edinburgh', '', 'S'),
        ('North Atlantic Ocean', '', 'S'),
        ('North Sea', '', 'S'),
        ('Norway', '', 'S'),
    ),
    ('Paris', '', 'L'): (
        ('Brest', '', 'L'),
        ('Burgundy', '', 'L'),
        ('Gascony', '', 'L'),
        ('Picardy', '', 'L'),
    ),
    ('Picardy', '', 'L'): (
        ('Belgium', '', 'L'),
        ('Brest', '', 'L'),
        ('Burgundy', '', 'L'),
        ('Paris', '', 'L'),
    ),
    ('Picardy', '', 'S'): (
        ('Belgium', '', 'S'),
        ('Brest', '', 'S'),
        ('English Channel', '', 'S'),
    ),
    ('Piedmont', '', 'L'): (
        ('Marseilles', '', 'L'),
        ('Tuscany', '', 'L'),
        ('Tyrolia', '', 'L'),
        ('Venice', '', 'L'),
    ),
    ('Piedmont', '', 'S'): (
        ('Gulf of Lyon', '', 'S'),
        ('Marseilles', '', 'S'),
        ('Tuscany', '', 'S'),
    ),
    ('Portugal', '', 'L'): (
        ('Spain', '', 'L'),
    ),
    ('Portugal', '', 'S'): (
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Spain', 'NC', 'S'),
        ('Spain', 'SC', 'S'),
    ),
    ('Prussia', '', 'L'): (
        ('Berlin', '', 'L'),
        ('Livonia', '', 'L'),
        ('Silesia', '', 'L'),
        ('Warsaw', '', 'L'),
    ),
    ('Prussia', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Berlin', '', 'S'),
        ('Livonia', '', 'S'),
    ),
    ('Rome', '', 'L'): (
        ('Apulia', '', 'L'),
        ('Naples', '', 'L'),
        ('Tuscany', '', 'L'),
        ('Venice', '', 'L'),
    ),
    ('Rome', '', 'S'): (
        ('Naples', '', 'S'),
        ('Tuscany', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
    ),
    ('Ruhr', '', 'L'): (
        ('Belgium', '', 'L'),
        ('Burgundy', '', 'L'),
        ('Holland', '', 'L'),
        ('Kiel', '', 'L'),
        ('Munich', '', 'L'),
    ),
    ('Rumania', '', 'L'): (
        ('Budapest', '', 'L'),
        ('Bulgaria', '', 'L'),
        ('Galicia', '', 'L'),
        ('Serbia', '', 'L'),
        ('Sevastopol', '', 'L'),
        ('Ukraine', '', 'L'),
    ),
    ('Rumania', '', 'S'): (
        ('Black Sea', '', 'S'),
        ('Bulgaria', 'EC', 'S'),
        ('Sevastopol', '', 'S'),
    ),
    ('Serbia', '', 'L'): (
        ('Albania', '', 'L'),
        ('Budapest', '', 'L'),
        ('Bulgaria', '', 'L'),
        ('Greece', '', 'L'),
        ('Rumania', '', 'L'),
        ('Trieste', '', 'L'),
    ),
    ('Sevastopol', '', 'L'): (
        ('Armenia', '', 'L'),
        ('Moscow', '', 'L'),
        ('Rumania', '', 'L'),
        ('Ukraine', '', 'L'),
    ),
    ('Sevastopol', '', 'S'): (
        ('Armenia', '', 'S'),
        ('Black Sea', '', 'S'),
        ('Rumania', '', 'S'),
    ),
    ('Silesia', '', 'L'): (
        ('Berlin', '', 'L'),
        ('Bohemia', '', 'L'),
        ('Galicia', '', 'L'),
        ('Munich', '', 'L'),
        ('Prussia', '', 'L'),
        ('Warsaw', '', 'L'),
    ),
    ('Skagerrak', '', 'S'): (
        ('Denmark', '', 'S'),
        ('North Sea', '', 'S'),
        ('Norway', '', 'S'),
        ('Sweden', '', 'S'),
    ),
    ('Smyrna', '', 'L'): (
        ('Ankara', '', 'L'),
        ('Armenia', '', 'L'),
        ('Constantinople', '', 'L'),
        ('Syria', '', 'L'),
    ),
    ('Smyrna', '', 'S'): (
        ('Aegean Sea', '', 'S'),
        ('Constantinople', '', 'S'),
        ('Eastern Mediterranean', '', 'S'),
        ('Syria', '', 'S'),
    ),
    ('Spain', '', 'L'): (
        ('Gascony', '', 'L'),
        ('Marseilles', '', 'L'),
        ('Portugal', '', 'L'),
    ),
    ('Spain', 'NC', 'S'): (
        ('Gascony', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Portugal', '', 'S'),
    ),
    ('Spain', 'SC', 'S'): (
        ('Gulf of Lyon', '', 'S'),
        ('Marseilles', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('Portugal', '', 'S'),
        ('Western Mediterranean', '', 'S'),
    ),
    ('St. Petersburg', '', 'L'): (
        ('Finland', '', 'L'),
        ('Livonia', '', 'L'),
        ('Moscow', '', 'L'),
        ('Norway', '', 'L'),
    ),
    ('St. Petersburg', 'NC', 'S'): (
        ('Barents Sea', '', 'S'),
        ('Norway', '', 'S'),
    ),
    ('St. Petersburg', 'SC', 'S'): (
        ('Finland', '', 'S'),
        ('Gulf of Bothnia', '', 'S'),
        ('Livonia', '', 'S'),
    ),
    ('Sweden', '', 'L'): (
        ('Denmark', '', 'L'),
        ('Finland', '', 'L'),
        ('Norway', '', 'L'),
    ),
    ('Sweden', '', 'S'): (
        ('Baltic Sea', '', 'S'),
        ('Denmark', '', 'S'),
        ('Finland', '', 'S'),
        ('Gulf of Bothnia', '', 'S'),
        ('Norway', '', 'S'),
        ('Skagerrak', '', 'S'),
    ),
    ('Syria', '', 'L'): (
        ('Armenia', '', 'L'),
        ('Smyrna', '', 'L'),
    ),
    ('Syria', '', 'S'): (
        ('Eastern Mediterranean', '', 'S'),
        ('Smyrna', '', 'S'),
    ),
    ('Trieste', '', 'L'): (
        ('Albania', '', 'L'),
        ('Budapest', '', 'L'),
        ('Serbia', '', 'L'),
        ('Tyrolia', '', 'L'),
        ('Venice', '', 'L'),
        ('Vienna', '', 'L'),
    ),
    ('Trieste', '', 'S'): (
        ('Adriatic Sea', '', 'S'),
        ('Albania', '', 'S'),
        ('Venice', '', 'S'),
    ),
    ('Tunisia', '', 'L'): (
        ('North Africa', '', 'L'),
    ),
    ('Tunisia', '', 'S'): (
        ('Ionian Sea', '', 'S'),
        ('North Africa', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
        ('Western Mediterranean', '', 'S'),
    ),
    ('Tuscany', '', 'L'): (
        ('Piedmont', '', 'L'),
        ('Rome', '', 'L'),
        ('Venice', '', 'L'),
    ),
    ('Tuscany', '', 'S'): (
        ('Gulf of Lyon', '', 'S'),
        ('Piedmont', '', 'S'),
        ('Rome', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
    ),
    ('Tyrolia', '', 'L'): (
        ('Bohemia', '', 'L'),
        ('Munich', '', 'L'),
        ('Piedmont', '', 'L'),
        ('Trieste', '', 'L'),
        ('Venice', '', 'L'),
        ('Vienna', '', 'L'),
    ),
    ('Tyrrhenian Sea', '', 'S'): (
        ('Gulf of Lyon', '', 'S'),
        ('Ionian Sea', '', 'S'),
        ('Naples', '', 'S'),
        ('Rome', '', 'S'),
        ('Tunisia', '', 'S'),
        ('Tuscany', '', 'S'),
        ('Western Mediterranean', '', 'S'),
    ),
    ('Ukraine', '', 'L'): (
        ('Galicia', '', 'L'),
        ('Moscow', '', 'L'),
        ('Rumania', '', 'L'),
        ('Sevastopol', '', 'L'),
        ('Warsaw', '', 'L'),
    ),
    ('Venice', '', 'L'): (
        ('Apulia', '', 'L'),
        ('Piedmont', '', 'L'),
        ('Rome', '', 'L'),
        ('Trieste', '', 'L'),
        ('Tuscany', '', 'L'),
        ('Tyrolia', '', 'L'),
    ),
    ('Venice', '', 'S'): (
        ('Adriatic Sea', '', 'S'),
        ('Apulia', '', 'S'),
        ('Trieste', '', 'S'),
    ),
    ('Vienna', '', 'L'): (
        ('Bohemia', '', 'L'),
        ('Budapest', '', 'L'),
        ('Galicia', '', 'L'),
        ('Trieste', '', 'L'),
        ('Tyrolia', '', 'L'),
    ),
    ('Wales', '', 'L'): (
        ('Liverpool', '', 'L'),
        ('London', '', 'L'),
        ('Yorkshire', '', 'L'),
    ),
    ('Wales', '', 'S'): (
        ('English Channel', '', 'S'),
        ('Irish Sea', '', 'S'),
        ('Liverpool', '', 'S'),
        ('London', '', 'S'),
    ),
    ('Warsaw', '', 'L'): (
        ('Galicia', '', 'L'),
        ('Livonia', '', 'L'),
        ('Moscow', '', 'L'),
        ('Prussia', '', 'L'),
        ('Silesia', '', 'L'),
        ('Ukraine', '', 'L'),
    ),
    ('Western Mediterranean', '', 'S'): (
        ('Gulf of Lyon', '', 'S'),
        ('Mid-Atlantic Ocean', '', 'S'),
        ('North Africa', '', 'S'),
        ('Spain', 'SC', 'S'),
        ('Tunisia', '', 'S'),
        ('Tyrrhenian Sea', '', 'S'),
    ),
    ('Yorkshire', '', 'L'): (
        ('Edinburgh', '', 'L'),
        ('Liverpool', '', 'L'),
        ('London', '', 'L'),
        ('Wales', '', 'L'),
    ),
    ('Yorkshire', '', 'S'): (
        ('Edinburgh', '', 'S'),
        ('London', '', 'S'),
        ('North Sea', '', 'S'),
    ),
}