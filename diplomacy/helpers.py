
convert = {'L': 'A', 'S': 'F'}

def unit(sr):
    return u"{0} {1}".format(convert[sr.sr_type], sr)
