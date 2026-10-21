BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

def encodeGeohash(lat: float, long: float, precision: int = 8) -> str:
    """Codifica coordenadas geográficas em uma string Geohash."""
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

def convertGeohashToGridPosition(geohash: str):
    """Converte um Geohash em índices inteiros de longitude e latitude."""
    lat = 0
    long = 0
    even = True
    for char in geohash:
        value = BASE32.index(char)
        for shift in range(4,-1,-1):
            bit = (value >> shift) & 1
            if even:
                long = (long << 1) | bit
            else:
                lat = (lat << 1) | bit

            even = not even
    return long, lat



def convertGridPositionToGeohash(lon_int: int, lat_int: int, precision: int) -> str:
    """Codifica índices inteiros de longitude e latitude como Geohash."""
    total_bits = precision * 5
    
    # Calcula exatamente quantos bits pertencem a cada eixo com base na precisão
    lon_bits = (total_bits + 1) // 2  # Ex: 25 bits -> 13 bits de Longitude
    lat_bits = total_bits // 2        # Ex: 25 bits -> 12 bits de Latitude
    
    result = []
    bit_buffer = 0
    bits_count = 0
    even = True
    
    # Reconstrói os 5 bits de cada caractere intercalando Longitude e Latitude
    for _ in range(total_bits):
        if even:
            # Pega o bit mais significativo (MSB) restante da Longitude
            lon_bits -= 1
            bit = (lon_int >> lon_bits) & 1
        else:
            # Pega o bit mais significativo (MSB) restante da Latitude
            lat_bits -= 1
            bit = (lat_int >> lat_bits) & 1
            
        even = not even
        
        # Empurra o bit extraído para o buffer de 5 bits
        bit_buffer = (bit_buffer << 1) | bit
        bits_count += 1
        
        # Quando completamos 5 bits, convertemos para o caractere Base32 correspondente
        if bits_count == 5:
            result.append(BASE32[bit_buffer])
            bit_buffer = 0
            bits_count = 0
            
    return "".join(result)

def getNeighborGeohashes(geohash: str):
    """Retorna os Geohashes da célula informada e de suas vizinhas."""
    neighbors = []
    adjacent_areas = [-1,0,1]
    long_line, lat_line = convertGeohashToGridPosition(geohash)
    for y in adjacent_areas:
        for x in adjacent_areas:
            neighbor = convertGridPositionToGeohash(long_line + x, lat_line + y, len(geohash))
            neighbors.append(neighbor)
    return neighbors

