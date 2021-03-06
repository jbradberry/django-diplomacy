
seasons = ('S', 'SR', 'F', 'FR', 'FA')

powers = {
    u'austria-hungary': u'Austria-Hungary',
    u'england': u'England',
    u'france': u'France',
    u'germany': u'Germany',
    u'italy': u'Italy',
    u'russia': u'Russia',
    u'turkey': u'Turkey'
}

inv_powers = {v: k for k, v in powers.items()}

territories = {
    u'adriatic-sea': u'Adriatic Sea',
    u'aegean-sea': u'Aegean Sea',
    u'albania': u'Albania',
    u'ankara': u'Ankara',
    u'apulia': u'Apulia',
    u'armenia': u'Armenia',
    u'baltic-sea': u'Baltic Sea',
    u'barents-sea': u'Barents Sea',
    u'belgium': u'Belgium',
    u'berlin': u'Berlin',
    u'black-sea': u'Black Sea',
    u'bohemia': u'Bohemia',
    u'brest': u'Brest',
    u'budapest': u'Budapest',
    u'bulgaria': u'Bulgaria',
    u'burgundy': u'Burgundy',
    u'clyde': u'Clyde',
    u'constantinople': u'Constantinople',
    u'denmark': u'Denmark',
    u'eastern-mediterranean': u'Eastern Mediterranean',
    u'edinburgh': u'Edinburgh',
    u'english-channel': u'English Channel',
    u'finland': u'Finland',
    u'galicia': u'Galicia',
    u'gascony': u'Gascony',
    u'greece': u'Greece',
    u'gulf-of-bothnia': u'Gulf of Bothnia',
    u'gulf-of-lyon': u'Gulf of Lyon',
    u'helgoland-bight': u'Helgoland Bight',
    u'holland': u'Holland',
    u'ionian-sea': u'Ionian Sea',
    u'irish-sea': u'Irish Sea',
    u'kiel': u'Kiel',
    u'liverpool': u'Liverpool',
    u'livonia': u'Livonia',
    u'london': u'London',
    u'marseilles': u'Marseilles',
    u'mid-atlantic-ocean': u'Mid-Atlantic Ocean',
    u'moscow': u'Moscow',
    u'munich': u'Munich',
    u'naples': u'Naples',
    u'north-africa': u'North Africa',
    u'north-atlantic-ocean': u'North Atlantic Ocean',
    u'north-sea': u'North Sea',
    u'norway': u'Norway',
    u'norwegian-sea': u'Norwegian Sea',
    u'paris': u'Paris',
    u'picardy': u'Picardy',
    u'piedmont': u'Piedmont',
    u'portugal': u'Portugal',
    u'prussia': u'Prussia',
    u'rome': u'Rome',
    u'ruhr': u'Ruhr',
    u'rumania': u'Rumania',
    u'serbia': u'Serbia',
    u'sevastopol': u'Sevastopol',
    u'silesia': u'Silesia',
    u'skagerrak': u'Skagerrak',
    u'smyrna': u'Smyrna',
    u'spain': u'Spain',
    u'st-petersburg': u'St. Petersburg',
    u'sweden': u'Sweden',
    u'syria': u'Syria',
    u'trieste': u'Trieste',
    u'tunisia': u'Tunisia',
    u'tuscany': u'Tuscany',
    u'tyrolia': u'Tyrolia',
    u'tyrrhenian-sea': u'Tyrrhenian Sea',
    u'ukraine': u'Ukraine',
    u'venice': u'Venice',
    u'vienna': u'Vienna',
    u'wales': u'Wales',
    u'warsaw': u'Warsaw',
    u'western-mediterranean': u'Western Mediterranean',
    u'yorkshire': u'Yorkshire'
}

inv_territories = {v: k for k, v in territories.items()}

subregions = {
    u'adriatic-sea.s': (u'Adriatic Sea', u'', u'S'),
    u'aegean-sea.s': (u'Aegean Sea', u'', u'S'),
    u'albania.l': (u'Albania', u'', u'L'),
    u'albania.s': (u'Albania', u'', u'S'),
    u'ankara.l': (u'Ankara', u'', u'L'),
    u'ankara.s': (u'Ankara', u'', u'S'),
    u'apulia.l': (u'Apulia', u'', u'L'),
    u'apulia.s': (u'Apulia', u'', u'S'),
    u'armenia.l': (u'Armenia', u'', u'L'),
    u'armenia.s': (u'Armenia', u'', u'S'),
    u'baltic-sea.s': (u'Baltic Sea', u'', u'S'),
    u'barents-sea.s': (u'Barents Sea', u'', u'S'),
    u'belgium.l': (u'Belgium', u'', u'L'),
    u'belgium.s': (u'Belgium', u'', u'S'),
    u'berlin.l': (u'Berlin', u'', u'L'),
    u'berlin.s': (u'Berlin', u'', u'S'),
    u'black-sea.s': (u'Black Sea', u'', u'S'),
    u'bohemia.l': (u'Bohemia', u'', u'L'),
    u'brest.l': (u'Brest', u'', u'L'),
    u'brest.s': (u'Brest', u'', u'S'),
    u'budapest.l': (u'Budapest', u'', u'L'),
    u'bulgaria.ec.s': (u'Bulgaria', u'EC', u'S'),
    u'bulgaria.l': (u'Bulgaria', u'', u'L'),
    u'bulgaria.sc.s': (u'Bulgaria', u'SC', u'S'),
    u'burgundy.l': (u'Burgundy', u'', u'L'),
    u'clyde.l': (u'Clyde', u'', u'L'),
    u'clyde.s': (u'Clyde', u'', u'S'),
    u'constantinople.l': (u'Constantinople', u'', u'L'),
    u'constantinople.s': (u'Constantinople', u'', u'S'),
    u'denmark.l': (u'Denmark', u'', u'L'),
    u'denmark.s': (u'Denmark', u'', u'S'),
    u'eastern-mediterranean.s': (u'Eastern Mediterranean', u'', u'S'),
    u'edinburgh.l': (u'Edinburgh', u'', u'L'),
    u'edinburgh.s': (u'Edinburgh', u'', u'S'),
    u'english-channel.s': (u'English Channel', u'', u'S'),
    u'finland.l': (u'Finland', u'', u'L'),
    u'finland.s': (u'Finland', u'', u'S'),
    u'galicia.l': (u'Galicia', u'', u'L'),
    u'gascony.l': (u'Gascony', u'', u'L'),
    u'gascony.s': (u'Gascony', u'', u'S'),
    u'greece.l': (u'Greece', u'', u'L'),
    u'greece.s': (u'Greece', u'', u'S'),
    u'gulf-of-bothnia.s': (u'Gulf of Bothnia', u'', u'S'),
    u'gulf-of-lyon.s': (u'Gulf of Lyon', u'', u'S'),
    u'helgoland-bight.s': (u'Helgoland Bight', u'', u'S'),
    u'holland.l': (u'Holland', u'', u'L'),
    u'holland.s': (u'Holland', u'', u'S'),
    u'ionian-sea.s': (u'Ionian Sea', u'', u'S'),
    u'irish-sea.s': (u'Irish Sea', u'', u'S'),
    u'kiel.l': (u'Kiel', u'', u'L'),
    u'kiel.s': (u'Kiel', u'', u'S'),
    u'liverpool.l': (u'Liverpool', u'', u'L'),
    u'liverpool.s': (u'Liverpool', u'', u'S'),
    u'livonia.l': (u'Livonia', u'', u'L'),
    u'livonia.s': (u'Livonia', u'', u'S'),
    u'london.l': (u'London', u'', u'L'),
    u'london.s': (u'London', u'', u'S'),
    u'marseilles.l': (u'Marseilles', u'', u'L'),
    u'marseilles.s': (u'Marseilles', u'', u'S'),
    u'mid-atlantic-ocean.s': (u'Mid-Atlantic Ocean', u'', u'S'),
    u'moscow.l': (u'Moscow', u'', u'L'),
    u'munich.l': (u'Munich', u'', u'L'),
    u'naples.l': (u'Naples', u'', u'L'),
    u'naples.s': (u'Naples', u'', u'S'),
    u'north-africa.l': (u'North Africa', u'', u'L'),
    u'north-africa.s': (u'North Africa', u'', u'S'),
    u'north-atlantic-ocean.s': (u'North Atlantic Ocean', u'', u'S'),
    u'north-sea.s': (u'North Sea', u'', u'S'),
    u'norway.l': (u'Norway', u'', u'L'),
    u'norway.s': (u'Norway', u'', u'S'),
    u'norwegian-sea.s': (u'Norwegian Sea', u'', u'S'),
    u'paris.l': (u'Paris', u'', u'L'),
    u'picardy.l': (u'Picardy', u'', u'L'),
    u'picardy.s': (u'Picardy', u'', u'S'),
    u'piedmont.l': (u'Piedmont', u'', u'L'),
    u'piedmont.s': (u'Piedmont', u'', u'S'),
    u'portugal.l': (u'Portugal', u'', u'L'),
    u'portugal.s': (u'Portugal', u'', u'S'),
    u'prussia.l': (u'Prussia', u'', u'L'),
    u'prussia.s': (u'Prussia', u'', u'S'),
    u'rome.l': (u'Rome', u'', u'L'),
    u'rome.s': (u'Rome', u'', u'S'),
    u'ruhr.l': (u'Ruhr', u'', u'L'),
    u'rumania.l': (u'Rumania', u'', u'L'),
    u'rumania.s': (u'Rumania', u'', u'S'),
    u'serbia.l': (u'Serbia', u'', u'L'),
    u'sevastopol.l': (u'Sevastopol', u'', u'L'),
    u'sevastopol.s': (u'Sevastopol', u'', u'S'),
    u'silesia.l': (u'Silesia', u'', u'L'),
    u'skagerrak.s': (u'Skagerrak', u'', u'S'),
    u'smyrna.l': (u'Smyrna', u'', u'L'),
    u'smyrna.s': (u'Smyrna', u'', u'S'),
    u'spain.l': (u'Spain', u'', u'L'),
    u'spain.nc.s': (u'Spain', u'NC', u'S'),
    u'spain.sc.s': (u'Spain', u'SC', u'S'),
    u'st-petersburg.l': (u'St. Petersburg', u'', u'L'),
    u'st-petersburg.nc.s': (u'St. Petersburg', u'NC', u'S'),
    u'st-petersburg.sc.s': (u'St. Petersburg', u'SC', u'S'),
    u'sweden.l': (u'Sweden', u'', u'L'),
    u'sweden.s': (u'Sweden', u'', u'S'),
    u'syria.l': (u'Syria', u'', u'L'),
    u'syria.s': (u'Syria', u'', u'S'),
    u'trieste.l': (u'Trieste', u'', u'L'),
    u'trieste.s': (u'Trieste', u'', u'S'),
    u'tunisia.l': (u'Tunisia', u'', u'L'),
    u'tunisia.s': (u'Tunisia', u'', u'S'),
    u'tuscany.l': (u'Tuscany', u'', u'L'),
    u'tuscany.s': (u'Tuscany', u'', u'S'),
    u'tyrolia.l': (u'Tyrolia', u'', u'L'),
    u'tyrrhenian-sea.s': (u'Tyrrhenian Sea', u'', u'S'),
    u'ukraine.l': (u'Ukraine', u'', u'L'),
    u'venice.l': (u'Venice', u'', u'L'),
    u'venice.s': (u'Venice', u'', u'S'),
    u'vienna.l': (u'Vienna', u'', u'L'),
    u'wales.l': (u'Wales', u'', u'L'),
    u'wales.s': (u'Wales', u'', u'S'),
    u'warsaw.l': (u'Warsaw', u'', u'L'),
    u'western-mediterranean.s': (u'Western Mediterranean', u'', u'S'),
    u'yorkshire.l': (u'Yorkshire', u'', u'L'),
    u'yorkshire.s': (u'Yorkshire', u'', u'S')
}

inv_subregions = {v: k for k, v in subregions.items()}

# For every territory, specify:
#   - the initial owning empire, or None
#   - whether the territory is a supply center
#   - the subname (in standard, the coast name or an empty string)
#       and subregion type (land or sea) of the initial unit, or None
starting_state = {
    u'adriatic-sea': (None, False, None),
    u'aegean-sea': (None, False, None),
    u'albania': (None, False, None),
    u'ankara': (u'turkey', True, (u'', u'S')),
    u'apulia': (u'italy', False, None),
    u'armenia': (u'turkey', False, None),
    u'baltic-sea': (None, False, None),
    u'barents-sea': (None, False, None),
    u'belgium': (None, True, None),
    u'berlin': (u'germany', True, (u'', u'L')),
    u'black-sea': (None, False, None),
    u'bohemia': (u'austria-hungary', False, None),
    u'brest': (u'france', True, (u'', u'S')),
    u'budapest': (u'austria-hungary', True, (u'', u'L')),
    u'bulgaria': (None, True, None),
    u'burgundy': (u'france', False, None),
    u'clyde': (u'england', False, None),
    u'constantinople': (u'turkey', True, (u'', u'L')),
    u'denmark': (None, True, None),
    u'eastern-mediterranean': (None, False, None),
    u'edinburgh': (u'england', True, (u'', u'S')),
    u'english-channel': (None, False, None),
    u'finland': (u'russia', False, None),
    u'galicia': (u'austria-hungary', False, None),
    u'gascony': (u'france', False, None),
    u'greece': (None, True, None),
    u'gulf-of-bothnia': (None, False, None),
    u'gulf-of-lyon': (None, False, None),
    u'helgoland-bight': (None, False, None),
    u'holland': (None, True, None),
    u'ionian-sea': (None, False, None),
    u'irish-sea': (None, False, None),
    u'kiel': (u'germany', True, (u'', u'S')),
    u'liverpool': (u'england', True, (u'', u'L')),
    u'livonia': (u'russia', False, None),
    u'london': (u'england', True, (u'', u'S')),
    u'marseilles': (u'france', True, (u'', u'L')),
    u'mid-atlantic-ocean': (None, False, None),
    u'moscow': (u'russia', True, (u'', u'L')),
    u'munich': (u'germany', True, (u'', u'L')),
    u'naples': (u'italy', True, (u'', u'S')),
    u'north-africa': (None, False, None),
    u'north-atlantic-ocean': (None, False, None),
    u'north-sea': (None, False, None),
    u'norway': (None, True, None),
    u'norwegian-sea': (None, False, None),
    u'paris': (u'france', True, (u'', u'L')),
    u'picardy': (u'france', False, None),
    u'piedmont': (u'italy', False, None),
    u'portugal': (None, True, None),
    u'prussia': (u'germany', False, None),
    u'rome': (u'italy', True, (u'', u'L')),
    u'ruhr': (u'germany', False, None),
    u'rumania': (None, True, None),
    u'serbia': (None, True, None),
    u'sevastopol': (u'russia', True, (u'', u'S')),
    u'silesia': (u'germany', False, None),
    u'skagerrak': (None, False, None),
    u'smyrna': (u'turkey', True, (u'', u'L')),
    u'spain': (None, True, None),
    u'st-petersburg': (u'russia', True, (u'SC', u'S')),
    u'sweden': (None, True, None),
    u'syria': (u'turkey', False, None),
    u'trieste': (u'austria-hungary', True, (u'', u'S')),
    u'tunisia': (None, True, None),
    u'tuscany': (u'italy', False, None),
    u'tyrolia': (u'austria-hungary', False, None),
    u'tyrrhenian-sea': (None, False, None),
    u'ukraine': (u'russia', False, None),
    u'venice': (u'italy', True, (u'', u'L')),
    u'vienna': (u'austria-hungary', True, (u'', u'L')),
    u'wales': (u'england', False, None),
    u'warsaw': (u'russia', True, (u'', u'L')),
    u'western-mediterranean': (None, False, None),
    u'yorkshire': (u'england', False, None)
}

# Define the connectivity of the map.
connectivity = {
    u'adriatic-sea.s': (u'albania.s', u'apulia.s', u'ionian-sea.s', u'trieste.s', u'venice.s'),
    u'aegean-sea.s': (u'bulgaria.sc.s', u'constantinople.s', u'eastern-mediterranean.s',
                      u'greece.s', u'ionian-sea.s', u'smyrna.s'),
    u'albania.l': (u'greece.l', u'serbia.l', u'trieste.l'),
    u'albania.s': (u'adriatic-sea.s', u'greece.s', u'ionian-sea.s', u'trieste.s'),
    u'ankara.l': (u'armenia.l', u'constantinople.l', u'smyrna.l'),
    u'ankara.s': (u'armenia.s', u'black-sea.s', u'constantinople.s'),
    u'apulia.l': (u'naples.l', u'rome.l', u'venice.l'),
    u'apulia.s': (u'adriatic-sea.s', u'ionian-sea.s', u'naples.s', u'venice.s'),
    u'armenia.l': (u'ankara.l', u'sevastopol.l', u'smyrna.l', u'syria.l'),
    u'armenia.s': (u'ankara.s', u'black-sea.s', u'sevastopol.s'),
    u'baltic-sea.s': (u'berlin.s', u'denmark.s', u'gulf-of-bothnia.s', u'kiel.s', u'livonia.s',
                      u'prussia.s', u'sweden.s'),
    u'barents-sea.s': (u'norway.s', u'norwegian-sea.s', u'st-petersburg.nc.s'),
    u'belgium.l': (u'burgundy.l', u'holland.l', u'picardy.l', u'ruhr.l'),
    u'belgium.s': (u'english-channel.s', u'holland.s', u'north-sea.s', u'picardy.s'),
    u'berlin.l': (u'kiel.l', u'munich.l', u'prussia.l', u'silesia.l'),
    u'berlin.s': (u'baltic-sea.s', u'kiel.s', u'prussia.s'),
    u'black-sea.s': (u'ankara.s', u'armenia.s', u'bulgaria.ec.s', u'constantinople.s',
                     u'rumania.s', u'sevastopol.s'),
    u'bohemia.l': (u'galicia.l', u'munich.l', u'silesia.l', u'tyrolia.l', u'vienna.l'),
    u'brest.l': (u'gascony.l', u'paris.l', u'picardy.l'),
    u'brest.s': (u'english-channel.s', u'gascony.s', u'mid-atlantic-ocean.s', u'picardy.s'),
    u'budapest.l': (u'galicia.l', u'rumania.l', u'serbia.l', u'trieste.l', u'vienna.l'),
    u'bulgaria.ec.s': (u'black-sea.s', u'constantinople.s', u'rumania.s'),
    u'bulgaria.l': (u'constantinople.l', u'greece.l', u'rumania.l', u'serbia.l'),
    u'bulgaria.sc.s': (u'aegean-sea.s', u'constantinople.s', u'greece.s'),
    u'burgundy.l': (u'belgium.l', u'gascony.l', u'marseilles.l', u'munich.l', u'paris.l',
                    u'picardy.l', u'ruhr.l'),
    u'clyde.l': (u'edinburgh.l', u'liverpool.l'),
    u'clyde.s': (u'edinburgh.s', u'liverpool.s', u'north-atlantic-ocean.s', u'norwegian-sea.s'),
    u'constantinople.l': (u'ankara.l', u'bulgaria.l', u'smyrna.l'),
    u'constantinople.s': (u'aegean-sea.s', u'ankara.s', u'black-sea.s', u'bulgaria.ec.s',
                          u'bulgaria.sc.s', u'smyrna.s'),
    u'denmark.l': (u'kiel.l', u'sweden.l'),
    u'denmark.s': (u'baltic-sea.s', u'helgoland-bight.s', u'kiel.s', u'north-sea.s',
                   u'skagerrak.s', u'sweden.s'),
    u'eastern-mediterranean.s': (u'aegean-sea.s', u'ionian-sea.s', u'smyrna.s', u'syria.s'),
    u'edinburgh.l': (u'clyde.l', u'liverpool.l', u'yorkshire.l'),
    u'edinburgh.s': (u'clyde.s', u'north-sea.s', u'norwegian-sea.s', u'yorkshire.s'),
    u'english-channel.s': (u'belgium.s', u'brest.s', u'irish-sea.s', u'london.s',
                           u'mid-atlantic-ocean.s', u'north-sea.s', u'picardy.s', u'wales.s'),
    u'finland.l': (u'norway.l', u'st-petersburg.l', u'sweden.l'),
    u'finland.s': (u'gulf-of-bothnia.s', u'st-petersburg.sc.s', u'sweden.s'),
    u'galicia.l': (u'bohemia.l', u'budapest.l', u'rumania.l', u'silesia.l', u'ukraine.l',
                   u'vienna.l', u'warsaw.l'),
    u'gascony.l': (u'brest.l', u'burgundy.l', u'marseilles.l', u'paris.l', u'spain.l'),
    u'gascony.s': (u'brest.s', u'mid-atlantic-ocean.s', u'spain.nc.s'),
    u'greece.l': (u'albania.l', u'bulgaria.l', u'serbia.l'),
    u'greece.s': (u'aegean-sea.s', u'albania.s', u'bulgaria.sc.s', u'ionian-sea.s'),
    u'gulf-of-bothnia.s': (u'baltic-sea.s', u'finland.s', u'livonia.s', u'st-petersburg.sc.s',
                           u'sweden.s'),
    u'gulf-of-lyon.s': (u'marseilles.s', u'piedmont.s', u'spain.sc.s', u'tuscany.s',
                        u'tyrrhenian-sea.s', u'western-mediterranean.s'),
    u'helgoland-bight.s': (u'denmark.s', u'holland.s', u'kiel.s', u'north-sea.s'),
    u'holland.l': (u'belgium.l', u'kiel.l', u'ruhr.l'),
    u'holland.s': (u'belgium.s', u'helgoland-bight.s', u'kiel.s', u'north-sea.s'),
    u'ionian-sea.s': (u'adriatic-sea.s', u'aegean-sea.s', u'albania.s', u'apulia.s',
                      u'eastern-mediterranean.s', u'greece.s', u'naples.s', u'tunisia.s',
                      u'tyrrhenian-sea.s'),
    u'irish-sea.s': (u'english-channel.s', u'liverpool.s', u'mid-atlantic-ocean.s',
                     u'north-atlantic-ocean.s', u'wales.s'),
    u'kiel.l': (u'berlin.l', u'denmark.l', u'holland.l', u'munich.l', u'ruhr.l'),
    u'kiel.s': (u'baltic-sea.s', u'berlin.s', u'denmark.s', u'helgoland-bight.s', u'holland.s'),
    u'liverpool.l': (u'clyde.l', u'edinburgh.l', u'wales.l', u'yorkshire.l'),
    u'liverpool.s': (u'clyde.s', u'irish-sea.s', u'north-atlantic-ocean.s', u'wales.s'),
    u'livonia.l': (u'moscow.l', u'prussia.l', u'st-petersburg.l', u'warsaw.l'),
    u'livonia.s': (u'baltic-sea.s', u'gulf-of-bothnia.s', u'prussia.s', u'st-petersburg.sc.s'),
    u'london.l': (u'wales.l', u'yorkshire.l'),
    u'london.s': (u'english-channel.s', u'north-sea.s', u'wales.s', u'yorkshire.s'),
    u'marseilles.l': (u'burgundy.l', u'gascony.l', u'piedmont.l', u'spain.l'),
    u'marseilles.s': (u'gulf-of-lyon.s', u'piedmont.s', u'spain.sc.s'),
    u'mid-atlantic-ocean.s': (u'brest.s', u'english-channel.s', u'gascony.s', u'irish-sea.s',
                              u'north-africa.s', u'north-atlantic-ocean.s', u'portugal.s',
                              u'spain.nc.s', u'spain.sc.s', u'western-mediterranean.s'),
    u'moscow.l': (u'livonia.l', u'sevastopol.l', u'st-petersburg.l', u'ukraine.l', u'warsaw.l'),
    u'munich.l': (u'berlin.l', u'bohemia.l', u'burgundy.l', u'kiel.l', u'ruhr.l', u'silesia.l',
                  u'tyrolia.l'),
    u'naples.l': (u'apulia.l', u'rome.l'),
    u'naples.s': (u'apulia.s', u'ionian-sea.s', u'rome.s', u'tyrrhenian-sea.s'),
    u'north-africa.l': (u'tunisia.l',),
    u'north-africa.s': (u'mid-atlantic-ocean.s', u'tunisia.s', u'western-mediterranean.s'),
    u'north-atlantic-ocean.s': (u'clyde.s', u'irish-sea.s', u'liverpool.s',
                                u'mid-atlantic-ocean.s', u'norwegian-sea.s'),
    u'north-sea.s': (u'belgium.s', u'denmark.s', u'edinburgh.s', u'english-channel.s',
                     u'helgoland-bight.s', u'holland.s', u'london.s', u'norway.s',
                     u'norwegian-sea.s', u'skagerrak.s', u'yorkshire.s'),
    u'norway.l': (u'finland.l', u'st-petersburg.l', u'sweden.l'),
    u'norway.s': (u'barents-sea.s', u'north-sea.s', u'norwegian-sea.s', u'skagerrak.s',
                  u'st-petersburg.nc.s', u'sweden.s'),
    u'norwegian-sea.s': (u'barents-sea.s', u'clyde.s', u'edinburgh.s', u'north-atlantic-ocean.s',
                         u'north-sea.s', u'norway.s'),
    u'paris.l': (u'brest.l', u'burgundy.l', u'gascony.l', u'picardy.l'),
    u'picardy.l': (u'belgium.l', u'brest.l', u'burgundy.l', u'paris.l'),
    u'picardy.s': (u'belgium.s', u'brest.s', u'english-channel.s'),
    u'piedmont.l': (u'marseilles.l', u'tuscany.l', u'tyrolia.l', u'venice.l'),
    u'piedmont.s': (u'gulf-of-lyon.s', u'marseilles.s', u'tuscany.s'),
    u'portugal.l': (u'spain.l',),
    u'portugal.s': (u'mid-atlantic-ocean.s', u'spain.nc.s', u'spain.sc.s'),
    u'prussia.l': (u'berlin.l', u'livonia.l', u'silesia.l', u'warsaw.l'),
    u'prussia.s': (u'baltic-sea.s', u'berlin.s', u'livonia.s'),
    u'rome.l': (u'apulia.l', u'naples.l', u'tuscany.l', u'venice.l'),
    u'rome.s': (u'naples.s', u'tuscany.s', u'tyrrhenian-sea.s'),
    u'ruhr.l': (u'belgium.l', u'burgundy.l', u'holland.l', u'kiel.l', u'munich.l'),
    u'rumania.l': (u'budapest.l', u'bulgaria.l', u'galicia.l', u'serbia.l',
                   u'sevastopol.l', u'ukraine.l'),
    u'rumania.s': (u'black-sea.s', u'bulgaria.ec.s', u'sevastopol.s'),
    u'serbia.l': (u'albania.l', u'budapest.l', u'bulgaria.l', u'greece.l', u'rumania.l',
                  u'trieste.l'),
    u'sevastopol.l': (u'armenia.l', u'moscow.l', u'rumania.l', u'ukraine.l'),
    u'sevastopol.s': (u'armenia.s', u'black-sea.s', u'rumania.s'),
    u'silesia.l': (u'berlin.l', u'bohemia.l', u'galicia.l', u'munich.l', u'prussia.l',
                   u'warsaw.l'),
    u'skagerrak.s': (u'denmark.s', u'north-sea.s', u'norway.s', u'sweden.s'),
    u'smyrna.l': (u'ankara.l', u'armenia.l', u'constantinople.l', u'syria.l'),
    u'smyrna.s': (u'aegean-sea.s', u'constantinople.s', u'eastern-mediterranean.s', u'syria.s'),
    u'spain.l': (u'gascony.l', u'marseilles.l', u'portugal.l'),
    u'spain.nc.s': (u'gascony.s', u'mid-atlantic-ocean.s', u'portugal.s'),
    u'spain.sc.s': (u'gulf-of-lyon.s', u'marseilles.s', u'mid-atlantic-ocean.s',
                    u'portugal.s', u'western-mediterranean.s'),
    u'st-petersburg.l': (u'finland.l', u'livonia.l', u'moscow.l', u'norway.l'),
    u'st-petersburg.nc.s': (u'barents-sea.s', u'norway.s'),
    u'st-petersburg.sc.s': (u'finland.s', u'gulf-of-bothnia.s', u'livonia.s'),
    u'sweden.l': (u'denmark.l', u'finland.l', u'norway.l'),
    u'sweden.s': (u'baltic-sea.s', u'denmark.s', u'finland.s', u'gulf-of-bothnia.s',
                  u'norway.s', u'skagerrak.s'),
    u'syria.l': (u'armenia.l', u'smyrna.l'),
    u'syria.s': (u'eastern-mediterranean.s', u'smyrna.s'),
    u'trieste.l': (u'albania.l', u'budapest.l', u'serbia.l', u'tyrolia.l', u'venice.l',
                   u'vienna.l'),
    u'trieste.s': (u'adriatic-sea.s', u'albania.s', u'venice.s'),
    u'tunisia.l': (u'north-africa.l',),
    u'tunisia.s': (u'ionian-sea.s', u'north-africa.s', u'tyrrhenian-sea.s',
                   u'western-mediterranean.s'),
    u'tuscany.l': (u'piedmont.l', u'rome.l', u'venice.l'),
    u'tuscany.s': (u'gulf-of-lyon.s', u'piedmont.s', u'rome.s', u'tyrrhenian-sea.s'),
    u'tyrolia.l': (u'bohemia.l', u'munich.l', u'piedmont.l', u'trieste.l', u'venice.l',
                   u'vienna.l'),
    u'tyrrhenian-sea.s': (u'gulf-of-lyon.s', u'ionian-sea.s', u'naples.s', u'rome.s',
                          u'tunisia.s', u'tuscany.s', u'western-mediterranean.s'),
    u'ukraine.l': (u'galicia.l', u'moscow.l', u'rumania.l', u'sevastopol.l', u'warsaw.l'),
    u'venice.l': (u'apulia.l', u'piedmont.l', u'rome.l', u'trieste.l', u'tuscany.l', u'tyrolia.l'),
    u'venice.s': (u'adriatic-sea.s', u'apulia.s', u'trieste.s'),
    u'vienna.l': (u'bohemia.l', u'budapest.l', u'galicia.l', u'trieste.l', u'tyrolia.l'),
    u'wales.l': (u'liverpool.l', u'london.l', u'yorkshire.l'),
    u'wales.s': (u'english-channel.s', u'irish-sea.s', u'liverpool.s', u'london.s'),
    u'warsaw.l': (u'galicia.l', u'livonia.l', u'moscow.l', u'prussia.l', u'silesia.l',
                  u'ukraine.l'),
    u'western-mediterranean.s': (u'gulf-of-lyon.s', u'mid-atlantic-ocean.s', u'north-africa.s',
                                 u'spain.sc.s', u'tunisia.s', u'tyrrhenian-sea.s'),
    u'yorkshire.l': (u'edinburgh.l', u'liverpool.l', u'london.l', u'wales.l'),
    u'yorkshire.s': (u'edinburgh.s', u'london.s', u'north-sea.s'),
}

# Group together the subregions into territories.
subregion_groups = {}
for subregion in subregions:
    subregion_groups.setdefault(subregion.split('.')[0], []).append(subregion)

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
