import os
import json
import csv
import argparse


def ring_area(coords):
    """Return polygon ring area using the shoelace formula."""
    area = 0.0
    if not coords:
        return 0.0
    for i in range(len(coords)):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % len(coords)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def polygon_metrics(rings):
    """Given a list of rings (first is exterior, rest are holes),
    return polygon area, hole area and hole percentage."""
    if not rings:
        return 0.0, 0.0, 0.0
    outer_area = ring_area(rings[0])
    hole_area = sum(ring_area(r) for r in rings[1:])
    polygon_area = outer_area - hole_area
    if polygon_area <= 0:
        hole_pct = 0.0
    else:
        hole_pct = (hole_area / polygon_area) * 100.0
    return polygon_area, hole_area, hole_pct


def process_geojson(path):
    """Process a geojson file and yield metrics for each polygon/multipolygon."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get('type') == 'FeatureCollection':
        features = data.get('features', [])
    else:
        features = [data]

    index = 0
    for feat in features:
        geom = feat.get('geometry', {})
        gtype = geom.get('type')
        coords = geom.get('coordinates', [])
        if gtype == 'Polygon':
            index += 1
            polygon_area, hole_area, hole_pct = polygon_metrics(coords)
            yield index, polygon_area, hole_area, hole_pct
        elif gtype == 'MultiPolygon':
            for poly in coords:
                index += 1
                polygon_area, hole_area, hole_pct = polygon_metrics(poly)
                yield index, polygon_area, hole_area, hole_pct
        else:
            # skip other geometry types
            continue


def main():
    parser = argparse.ArgumentParser(description='Report hole areas in polygons within GeoJSON files.')
    parser.add_argument('folder', help='Folder containing GeoJSON files')
    parser.add_argument('-o', '--output', default='hole_report.csv', help='Output CSV filename')
    args = parser.parse_args()

    rows = []
    for filename in os.listdir(args.folder):
        if not filename.lower().endswith(('.json', '.geojson')):
            continue
        path = os.path.join(args.folder, filename)
        for index, polygon_area, hole_area, hole_pct in process_geojson(path):
            rows.append({'file': filename,
                         'feature_index': index,
                         'polygon_area': polygon_area,
                         'hole_area': hole_area,
                         'hole_percent': hole_pct})

    fieldnames = ['file', 'feature_index', 'polygon_area', 'hole_area', 'hole_percent']
    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f'Report written to {args.output}')


if __name__ == '__main__':
    main()
