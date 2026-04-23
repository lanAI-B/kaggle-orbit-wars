import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet

def agent(obs):
    moves = []
    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    raw_planets = obs.get("planets", []) if isinstance(obs, dict) else obs.planets
    raw_fleets = obs.get("fleets", []) if isinstance(obs, dict) else obs.fleets
    
    planets = [Planet(*p) for p in raw_planets]
    my_planets = [p for p in planets if p.owner == player]
    targets = [p for p in planets if p.owner != player]

    if not targets or not my_planets:
        return moves

    # 1. Track our existing fleets and their likely destinations
    # format: {target_id: total_incoming_ships}
    incoming_support = {}
    for f in raw_fleets:
        f_owner = f[1]
        if f_owner == player:
            f_angle = f[4]
            f_from_id = f[5]
            f_ships = f[6]
            
            # Predict which planet this fleet is heading to
            # (In Orbit Wars, they fly straight at the angle they were launched)
            # For simplicity, we'll assume the agent targets the center of planets
            from_p = next((p for p in planets if p.id == f_from_id), None)
            if from_p:
                for t in targets:
                    angle_to_t = math.atan2(t.y - from_p.y, t.x - from_p.x)
                    # If the angle is very close, it's likely the target
                    if abs(angle_to_t - f_angle) < 0.01:
                        incoming_support[t.id] = incoming_support.get(t.id, 0) + f_ships
                        break

    # 2. Evaluate targets and commit resources
    # We want to conquer the most valuable targets first
    targets.sort(key=lambda t: t.production / max(1, t.ships), reverse=True)

    # 3. Ship allocation logic
    for t in targets:
        # Distance and travel time
        # We find our closest planet to provide the most accurate travel time
        closest_mine = min(my_planets, key=lambda m: math.hypot(m.x - t.x, m.y - t.y))
        dist = math.hypot(closest_mine.x - t.x, closest_mine.y - t.y)
        travel_time = dist / 1.0 # Base speed
        
        # Predict target strength at arrival
        predicted_ships = t.ships + (t.production * travel_time)
        already_sent = incoming_support.get(t.id, 0)
        
        # Still need more?
        needed = int(predicted_ships + 10 - already_sent)
        
        if needed > 0:
            # Try to fulfill this 'needed' quota from all our planets
            for mine in sorted(my_planets, key=lambda m: math.hypot(m.x - t.x, m.y - t.y)):
                if needed <= 0: break
                
                # We leave a small garrison (20% or 5 ships) for defense
                available = max(0, mine.ships - max(5, int(mine.radius * 2)))
                
                if available > 0:
                    amount = min(available, needed)
                    angle = math.atan2(t.y - mine.y, t.x - mine.x)
                    moves.append([mine.id, angle, amount])
                    needed -= amount
                    # Update available ships for this mine for next target in this frame
                    mine_list = list(mine)
                    mine_list[5] -= amount # index 5 is ships
                    # Note: this is a local hack to the mine object for this loop

    return moves
