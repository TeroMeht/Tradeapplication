


# Laskee positio koon kun tiedetään nämä
def calculate_position_size(entry_price, stop_price, risk):

    try:
        risk_per_unit = entry_price - stop_price
        if risk_per_unit == 0:
            raise ValueError("Entry price and stop price cannot be the same.")
        
        position_size = abs(int(risk / risk_per_unit))  # force integer
        return position_size
    
    except Exception as e:
        print("Error calculating position size:", e)
        return None