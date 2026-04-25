#Consulta 1
def q1_count(zone_id, confidence_min=0.0):
    records = date[zone_id] #registros precargados para la zona
    return sum(1 for r in records if r.confidence >= confidence_min)

#Consulta 2
def q2_area(zone_id, confidence_min=0.0):
    areas = [r.area for r in date[zone_id] if r.confidence >= confidence_min]
    return {"avg_area": mean(areas), "total_area": sum(areas), "n": len}

#Consulta 3
def q3_density(zone_id, confidence_min=0.0):
    count = q1_count(zone_id, confidence_min)
    area_km2 = zone_area_km2[zone_id]
    return count / area_km2

#Consulta 4
def q4_compare(zone_a, zone_b, confidence_min=0.0):
    da = q3_density(zone_a, confidence_min)
    db = q3_density(zone_b, confidence_min)
    return {"zone_a":da, "zone_b":db, "winner":zone_a if da > db else zone_b}

def q5_confidence_dist(zone_id, bins=5):
    scores = [r.confidence for r in date[zone_id]]
    counts, edges = histogram(scores, bins=bins, range=(0, 1))
    return [{"bucket":i, "min":edges[i], "max":edges[i+1], "count":counts[i]} for i in range(bins)]
