from flask import Flask, request, jsonify
from backtester import backtest_straddle  # Import your strategy here
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/backtest', methods=['POST'])
def run_backtest():
    data = request.json
    start_date = data['start_date']
    duration = int(data['duration'])
    cash = float(data['cash'])
    
    # Run the backtest
    pnl, final_cash, daily_values = backtest_straddle(start_date, duration, cash)
    
    return jsonify({
        'pnl': pnl,
        'final_cash': final_cash,
        'daily_values': daily_values
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
