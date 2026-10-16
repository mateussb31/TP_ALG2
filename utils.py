BASE32 = "0123456789bcdefghjkmnopqrstuvwxyz"

def geohashConverter(lat: float, long: float, precision: int = 8) -> str:
    lat_range = [-90.0,90.0]
    long_range = [-180.0,180.0]
    even = True
    group = 0
    bits = 0
    result = ""
    center = 0
    while len(result) <  precision:
        if even:
            center = (long_range[0] + long_range[1])/2
            if long <= center:
                long_range[1] = center
            else:
                group |= (1 << (4 - bits))
                long_range[0] = center
        else:
            center = (lat_range[0]+lat_range[1])/2
            if lat <= center:
                lat_range[1] = center
            else:
                group |= (1 <<(4-bits))
                lat_range[0] = center
        even = not even
        if bits == 4:
            result+=BASE32[group]
            bits = 0
            group = 0
        else:
            bits +=1
    return result
