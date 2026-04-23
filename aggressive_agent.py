import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet

def agent(obs):
    moves = []
    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    raw_planets = obs.get("planets", []) if isinstance(obs, dict) else obs.planets
    planets = [Planet(*p) for p in raw_planets]

    my_planets = [p for p in planets if p.owner == player]
    targets = [p for p in planets if p.owner != player]

    if not targets:
        return moves

    # Constants from game rules
    SPEED_PER_SHIP = 1.0 # 1 ship = 1 unit/turn (capped at 6)
    
    for mine in my_planets:
        # Find the best target (highest production, lowest cost)
        best_target = None
        min_cost = float("inf")
        
        for t in targets:
            dist = math.hypot(mine.x - t.x, mine.y - t.y)
            
            # Predict how many ships the target will have when we arrive
            # We assume speed is 1 for now (conservative)
            travel_time = dist / 1.0 
            predicted_ships = t.ships + (t.production * travel_time)
            
            # Cost is ships needed + distance penalty (don't over-extend)
            cost = predicted_ships + (dist * 0.1)
            
            if cost < min_cost:
                min_cost = cost
                best_target = t
                target_arrival_ships = predicted_ships

        if best_target and mine.ships > target_arrival_ships + 5:
            angle = math.atan2(best_target.y - mine.y, best_target.x - mine.x)
            ships_to_send = int(target_arrival_ships + 5)
            
            # Ensure we don't send more than we have
            ships_to_send = min(ships_to_send, mine.ships - 1)
            
            moves.append([mine.id, angle, ships_to_send])

    return moves
