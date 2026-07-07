# Spatial And Travel System

## Purpose

Dungeoneer campaigns need real spatial reasoning. In this campaign, geography is
not backdrop: sea travel and airship travel are common, and PCs can gain a boat
early. The DM must understand distance, containment, borders, neighboring towns,
ports, routes, travel time, weather exposure, faction waters, and how news or
danger moves through the world.

This subsystem is required. It is not optional garnish or a future GIS curiosity.

## Core Principle

Spatial data is a projection over canon, not canon itself.

Canon remains:

- world definitions imported from DWD
- accepted events
- reviewed patches
- rules-owned mechanical state

The spatial system stores queryable projections and indexes derived from that
canon. If a route, border, port, faction territory, hazard, or location geometry
changes, the change is represented by a definition/event/patch first; PostGIS and
pgRouting tables are rebuilt or incrementally updated from that source.

## Required Stack

Use the existing Postgres database with these required extensions:

- **PostGIS** for geometry, containment, distance, intersection, adjacency, and
  map feature indexing.
- **pgRouting** for travel-route graph solving.

PostGIS Topology is allowed for map-authoring consistency where it helps
(coastlines, borders, shared region edges), but it is not the default travel graph.
Travel routes need mode-specific costs, constraints, risk, seasonality, and
fictional policy. pgRouting over explicit route tables is the primary route
solver.

Use PostGIS `geometry` as the default. Fantasy maps, local maps, hex maps, city
maps, sea charts, and airship corridors usually live in authored coordinate
systems, not Earth lat/lon. Use `geography` only for imported real-world maps or a
world deliberately authored in real coordinates.

## Scale Model

Spatial reasoning has three scales:

- **World/region scale:** countries, islands, coastlines, waters, mountain ranges,
  faction territories, ports, trade lanes, air corridors, and weather belts.
- **Local/site scale:** towns, districts, harbors, docks, castles, dungeons,
  entrances, rooms, local hazards, and hidden routes.
- **Encounter/battle scale:** grids, tokens, line of sight, cover, and tactical
  movement. This stays rules-owned, but can reference spatial features when a
  battle map is anchored to a location.

The same location entity can have multiple spatial representations at different
scales. A city may be a point on the world map, a polygon on a regional map, and a
set of districts on a city map.

## Canonical Concepts

Add these concepts to DWD and projections:

```text
spatial_reference      map/projection/coordinate-space metadata
spatial_feature        geometry-backed feature derived from a location, region,
                       route, hazard, territory, or authored map layer
route_node             graph node: port, anchorage, airship tower, city gate,
                       waypoint, pass, ford, canal lock
route_edge             graph edge: sea lane, river segment, road, air corridor,
                       canal, mountain pass, secret route
travel_profile         mode and vehicle profile: foot, horse, ship, airship,
                       rowboat, riverboat, cargo vessel
travel_plan            proposed route + ETA + costs + risk summary
territory              political/factional/control area, usually polygonal
hazard_zone            reef, storm belt, pirate waters, restricted airspace,
                       monster territory, planar instability
```

These are not all top-level entity kinds. Use top-level entities when the object
has lifecycle and narrative identity; use spatial features and route graph rows
for derived map/query structures.

## Spatial References

Every geometry is tied to a coordinate space.

```yaml
schema: dwd.spatial_reference.v1
id: spatial_ref:caelora_world_map
name: Caelora World Map
kind: fantasy_planar
units: mile
srid: 990001
origin: authored_map
precision: approximate
source_refs:
  - source:homebrew_world_map
```

Precision values:

```text
exact
approximate
symbolic
unknown
```

Rules:

- Do not invent precision. A hand-drawn map is usually `approximate`.
- Distinguish geographic distance from travel time.
- Store source/provenance for authored, imported, inferred, and generated geometry.
- Multiple spatial references may exist for one world.

## Location Spatial Facet

Locations keep their narrative identity in the entity model and add a spatial
facet when they can be mapped.

```yaml
id: loc:caelport
kind: location
schema: dwd.location.v1
name: Caelport
parent: region:brightwater_coast
scale: city
facets:
  spatial:
    spatial_ref: spatial_ref:caelora_world_map
    representation: polygon
    precision: approximate
    feature: spatial_feature:caelport.city_polygon
    ports:
      - route_node:port.caelport.deepwater
      - route_node:port.caelport.fisher_quay
    airship_moorings:
      - route_node:airship.caelport.high_tower
```

Containment remains semantic in DWD (`parent`) and queryable in PostGIS. When they
disagree, validators flag the contradiction.

## Travel Graph

Travel is mode-aware. "Far away" is not one number.

```yaml
schema: dwd.route_edge.v1
id: route:sea.caelport_to_morwyn_crossing
mode: sea
source: route_node:port.caelport.deepwater
target: route_node:port.morwyn.harbor
geometry: spatial_feature:sea_lane.caelport_morwyn
distance:
  value: 180
  unit: mile
base_duration:
  value: 3
  unit: day
bidirectional: true
constraints:
  min_vessel: coastal_sloop
  forbidden_tags: [rowboat]
seasonality:
  storm_season:
    duration_multiplier: 1.8
    risk_tags: [storm, delay, ship_damage]
risk_profile:
  baseline: moderate
  hazards: [hazard:glass_teeth_reef, faction:ash_ledger.patrols]
visibility:
  known_to: table
precision: approximate
source_refs:
  - source:caelora_sea_chart
```

Route edges are data, not rules. Route solving uses pgRouting; final adjudication
uses Dungeoneer contracts for vessel capability, weather, faction risk, player
choice, and time advancement.

## Travel Modes

Required first-class travel modes:

```text
walk
road
horse
river
sea
airship
canal
secret
magical
```

Sea travel tracks:

- ports, anchorages, straits, canals, reefs, currents, tides, and trade winds
- known lanes versus open-water shortcuts
- vessel draft, cargo, speed, crew, seaworthiness, and supply range
- faction waters, patrol zones, pirate zones, blockades, and customs checks
- seasonal weather and storm belts
- news, rumor, and faction-clock propagation by shipping lane

Airship travel tracks:

- mooring towers, landing fields, altitude bands, and resupply stops
- mountain passes, storm belts, restricted airspace, signal range, and visibility
- fuel/range constraints and faction air-control zones
- route risk from weather, monsters, anti-air defenses, customs, or secrecy

## Required Tools

The DM, loremasters, dreaming workers, and operator CLI use typed tools:

```text
world.spatial.where_is(entity_or_location)
world.spatial.contains(point_or_location)
world.spatial.nearby(location, radius, filters)
world.spatial.neighbors(region_or_location, relation)
world.spatial.distance(from, to, metric)
world.travel.route(from, to, mode, travel_profile)
world.travel.eta(route, season, weather, vehicle, crew)
world.travel.risks(route, faction_context, secrecy)
world.travel.reachable_from(location, duration, mode, travel_profile)
world.travel.news_reach(event, elapsed_time, channels)
```

Tool outputs must include:

- route or feature IDs
- distance and duration estimates
- assumptions and precision
- blocked/unsafe/unknown segments
- source/provenance
- visibility/audience guardrails

## Events And Projections

Spatial/travel projections are rebuilt from accepted events and definitions.

Relevant event types:

```text
location.changed
spatial.feature.updated
route.edge.updated
route.closed
route.opened
travel.started
travel.progressed
travel.completed
travel.interrupted
territory.changed
hazard.changed
weather.changed
```

Rules:

- Travel that changes world time emits events.
- A proposed route is not canon until chosen or accepted.
- Travel plans are projections/proposals; travel execution is event-sourced.
- Route closures, blockades, storms, and faction territory changes are world state
  and can be advanced by dreaming.

## Integration Points

**World schema.** Add spatial facets to locations/regions, route nodes/edges,
travel profiles, territories, hazard zones, and validators.

**Rules engine.** Keeps tactical/battle position ownership. It may call spatial
tools for overland/sea/air travel, pursuit, chase distance, or encounter setup,
but canonical combat positioning remains rules-owned.

**Orchestration.** The DM uses spatial tools when players ask where something is,
how far away it is, what neighbors it, how long travel takes, or what routes are
safe/secret.

**Loremasters.** Region, sea, faction, and route loremasters can be forked or
prepared from spatial projections. They cite canon and spatial source refs.

**Dreaming.** Advances off-screen travel, faction patrols, blockades, rumor/news
spread, weather/hazard changes, and route consequences.

**Frontend.** Shared display can show maps, route previews, travel clocks, and
public journey cards. Operator UI needs spatial inspection and correction tools.

**Deployment.** The state service must enable PostGIS and pgRouting in every
supported profile. A profile without those extensions is unsupported.

## Validators

Minimum validators:

- No spatial feature references dangling locations, regions, factions, or routes.
- Location containment (`parent`) and spatial containment do not contradict unless
  explicitly marked approximate/symbolic.
- Route nodes referenced by edges exist and have compatible spatial references.
- Travel edges have a mode, source, target, cost/duration model, and provenance.
- Sea routes start/end at ports, anchorages, or explicit open-water waypoints.
- Airship routes start/end at moorings, landing zones, or explicit waypoints.
- A route closure or blockade cannot affect an unknown route.
- A travel event cannot move an actor/vehicle along an impossible route without an
  override or explicit magical exception.

## Build Order

Phase 0:

- Enable PostGIS and pgRouting in the state database profile.
- Define Pydantic/JSON Schema contracts for spatial references, spatial facets,
  route nodes, route edges, travel profiles, travel plans, territories, and hazards.
- Add DWD syntax for authored spatial data.
- Add import validators for containment, route graph integrity, and provenance.

Phase 1:

- Implement basic spatial inspection tools: `where_is`, `nearby`, `contains`,
  `neighbors`, and `distance`.
- Seed the first campaign region with ports, nearby towns, faction waters, and the
  early boat's basic travel profile.
- Include spatial summaries in location and region loremaster capsules.

Phase 2:

- Implement pgRouting-backed `world.travel.route`, `eta`, `risks`, and
  `reachable_from`.
- Add travel events and world-time advancement.
- Add sea/airship route constraints, weather/season modifiers, and faction-risk
  overlays.

Phase 3+:

- Add map UI overlays, route previews, travel cards, and operator correction tools.
- Add richer weather, currents, trade winds, rumor propagation, and faction patrol
  simulation.
