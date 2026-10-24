#!/usr/bin/env -S python3 -I
"""geo/precinct_blocks.json (from compact.py blocks) + TIGER tabblock20 dbf -> geo/block_pts.json {GEOID:[lon,lat]}"""
import json, sys, os, shapefile
geo, tl = sys.argv[1], sys.argv[2]
pb = json.load(open(os.path.join(geo, 'precinct_blocks.json')))
need = {b for c in pb.values() for info in c.values() for b, _ in info['blocks']}
sf = shapefile.Reader(tl)
pts = {}
for rec in sf.iterRecords(fields=['GEOID20', 'INTPTLAT20', 'INTPTLON20']):
    if rec[0] in need: pts[rec[0]] = [float(rec[2]), float(rec[1])]
json.dump(pts, open(os.path.join(geo, 'block_pts.json'), 'w'), separators=(',', ':'))
print('blocks needed', len(need), 'found', len(pts), 'missing', len(need - set(pts)))
