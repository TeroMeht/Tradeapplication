from flask import Flask, request, jsonify
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)


@dataclass
class Order:
    symbol: str
    action: str
    position_size: int
    entry_price: float
    stop_price: float

# Apufunktiot place orderille. Tää rakentaa orderin joka lähtee IB:lle
def handle_place_order_request(data: dict):

    try:
        # Parse JSON data from the request
        data = request.json

        # Validate required fields
        required_fields = ['symbol', 'entry_price', 'stop_price', 'position_size']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Extract the order data from the request
        symbol = data['symbol']
        entry_price = float(data['entry_price'])  # Convert entry_price to float    
        stop_price = float(data['stop_price'])      # Convert stp_price to float
        position_size = int(data['position_size'])  # Convert position_size to int

     

        logger.info(f"Entry Price: {entry_price},  Stop Price: {stop_price}")
        # Determine action and order type based on price conditions
        if entry_price > stop_price:  # If entry price is higher than both limit and stop price
            action = 'BUY'
        elif entry_price < stop_price:  # If entry price is lower than both limit and stop price
            action = 'SELL'
        else:
            # If no condition is met (e.g., entry price is between limit and stop prices)
            raise ValueError("Invalid price conditions. Entry price does not match expected thresholds.")


    except Exception as e:
        logger.error(f"Error handling place order request: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    return Order(symbol=symbol,
                action=action,
                position_size=position_size,
                entry_price=entry_price,
                stop_price=stop_price
            )
