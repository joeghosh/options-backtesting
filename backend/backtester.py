import pandas as pd
import numpy as np
from datetime import timedelta
import time
import math
from pandas.tseries.offsets import BDay
from datetime import datetime
pd.options.mode.chained_assignment = None

class OptionStrategy:
    def __init__(self, initial_cash, data, start_date, duration):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.data = data
        self.start_date = pd.to_datetime(start_date, format='%Y-%m-%d', errors='coerce')
        self.duration = duration
        self.position = None
        self.daily_values = {}
        self.expiration_date = self.start_date + timedelta(days=self.duration)

    def find_closest_option(self, option_type, quote_date, strike_price, expiry_date, must_find=True):
        """Find the option contract closest to being at-the-money"""
        quote_date = pd.Timestamp(quote_date).normalize()
        original_expiry_date = pd.Timestamp(expiry_date).normalize()

        # Adjust dates to the nearest previous business day if they fall on a weekend
        quote_date = quote_date - BDay(0)
        expiry_date = original_expiry_date - BDay(0)

        # Convert the adjusted dates back to string format to match DataFrame
        quote_date_str = quote_date.strftime('%Y-%m-%d')
        expiry_date_str = expiry_date.strftime('%Y-%m-%d')

        # Filter the DataFrame based on the adjusted quote_date
        filtered_df = self.data[self.data['QUOTE_DATE'] == quote_date_str]

        if filtered_df.empty:
            if not (must_find):
                return None
            raise Exception("Retry program with different params - nothing for those dates")  # No matching entries found for the quote date

        df_expiry_dates = pd.to_datetime(filtered_df['EXPIRE_DATE']).dt.normalize()
        # Check if the expiry date exists in the filtered DataFrame
        if expiry_date_str not in filtered_df['EXPIRE_DATE']:
            # Find the nearest expiry date
            # filtered_df['EXPIRY_DIFF'] = abs(pd.to_datetime(filtered_df['EXPIRE_DATE']) - original_expiry_date)
            # nearest_expiry = filtered_df.loc[filtered_df['EXPIRY_DIFF'].idxmin(), 'EXPIRE_DATE']

            filtered_df['EXPIRY_DIFF'] = abs(df_expiry_dates - original_expiry_date)
            nearest_expiry = filtered_df.loc[filtered_df['EXPIRY_DIFF'].idxmin(), 'EXPIRE_DATE']
            nearest_expiry_date = pd.Timestamp(nearest_expiry).normalize()
            
            if nearest_expiry_date != original_expiry_date:
                print("had to substitute date")
            #     # Only prompt if the actual date is different
            #     print(f"No exact match found for expiry date {expiry_date_str}.")
            #     print(f"The nearest available expiry date is {nearest_expiry_date.strftime('%Y-%m-%d')}.")
            #     user_confirm = input("Do you want to use this expiry date? (y/n): ").lower().strip()
                
            #     if user_confirm == 'y':
            #         expiry_date_str = nearest_expiry_date.strftime('%Y-%m-%d')
            #         new_expiry_date = nearest_expiry_date
            #     else:
            #         raise Exception("Retry program with different params - that you're happy with >:(")  # User didn't confirm, so we kick them out
            # else:
                # If the date is the same (just different time format), use it without prompting
            expiry_date_str = nearest_expiry_date.strftime('%Y-%m-%d')
                
        else:
            new_expiry_date = expiry_date

        # Re-filter the DataFrame with the confirmed expiry date
        result_df = filtered_df[filtered_df['EXPIRE_DATE'] == expiry_date_str]
        
        # Find the closest strike price
        result_df['STRIKE_DIFF'] = abs(result_df['STRIKE'] - strike_price)
        closest_strike = result_df.loc[result_df['STRIKE_DIFF'].idxmin(), 'STRIKE']
        
        # Filter further based on the closest strike price
        result = result_df[result_df['STRIKE'] == closest_strike]


        if option_type == 'call':
            all_options = result[result['C_BID'].notna()]  # Ensure call data is available
            all_options['distance'] = abs(all_options['STRIKE'] - strike_price)
            closest = all_options.loc[all_options['distance'].idxmin()]
        else:
            all_options = result[result['P_BID'].notna()]  # Ensure put data is available
            all_options['distance'] = abs(all_options['STRIKE'] - strike_price)
            closest = all_options.loc[all_options['distance'].idxmin()]

        return closest

    def reevaluate_position_daily(self):
        """Reevaluate all option positions each business day until the latest expiration"""

        # TODO: Look into why some days dont find any kind of actual value for the option... are they just not listed??
        # TODO: Values in the graph dont match with final pnl values. final things are right so not sure what going on
        daily_values = []
        current_date = self.start_date
        end_date = max(
            max(pd.Timestamp(call['expiry']) for call in self.position['calls']),
            max(pd.Timestamp(put['expiry']) for put in self.position['puts'])
        )

        while current_date <= end_date:
            print(current_date)
            # Skip weekends
            if current_date.dayofweek < 5:  # Monday = 0, Friday = 4
                date_obj = datetime.strptime(str(current_date), "%Y-%m-%d %H:%M:%S")
                formatted_date = f"{date_obj.day}/{date_obj.month}"
                daily_value = {
                    'date': formatted_date,
                    'calls': [],
                    'puts': [],
                    'total_value': 0
                }

                # Evaluate calls
                for call in self.position['calls']:
                    option_data = self.find_closest_option(
                        'call',
                        current_date,
                        call['strike'],
                        call['expiry'],
                        must_find=False
                    )

                    if option_data is not None:
                        call_value = float(option_data['C_BID']) * call['size'] #this might be an issue with how the actual val is calculated
                        daily_value['calls'].append({
                            'expiry': call['expiry'],
                            'strike': call['strike'],
                            'value': call_value,
                            'implied_vol': option_data['C_IV'],
                            'size': call['size']
                        })
                        daily_value['total_value'] += float(call_value)
                    else:
                        daily_value['calls'].append({
                            'expiry': "N/A",
                            'strike': "N/A",
                            'value': "N/A",
                            'implied_vol': "N/A",
                            'size': "N/A"
                        })
                        daily_value['total_value'] += 0

                # Evaluate puts
                for put in self.position['puts']:
                    option_data = self.find_closest_option(
                        'put',
                        current_date,
                        put['strike'],
                        put['expiry'],
                        must_find=False
                    )

                    if option_data is not None:
                        put_value = float(option_data['P_BID']) * put['size']
                        daily_value['puts'].append({
                            'expiry': put['expiry'],
                            'strike': put['strike'],
                            'value': put_value,
                            'implied_vol': option_data['P_IV'],
                            'size': put['size']
                        })
                        daily_value['total_value'] += float(put_value)
                    else:
                        daily_value['puts'].append({
                            'expiry': "N/A",
                            'strike': "N/A",
                            'value': "N/A",
                            'implied_vol': "N/A",
                            'size': "N/A"
                        })
                        daily_value['total_value'] += 0

                daily_values.append(daily_value)

            # Move to the next day
            current_date += pd.Timedelta(days=1)

        return daily_values

    def close_position(self):
        """Close all option positions at their respective expiration dates"""
        total_exit_price = 0
        total_entry_price = 0

        # Given we carry everything to expiration, find underlying price on final day to use as value for stock.
        expiry_price = self.data[self.data['QUOTE_DATE'] == self.expiration_date]['UNDERLYING_LAST'].values[0]
        print("EXPIRY STUFF")
        print(expiry_price)

        # Process calls
        for call in self.position['calls']:
            expiry_data = self.data[self.data['QUOTE_DATE'] == call['expiry']]
            if not expiry_data.empty:
                S = expiry_data['UNDERLYING_LAST'].values[0]  # underlying price at expiration
                K = call['strike']
                call_value = max(0, S - K)
                exit_price = call_value * call['size']
                print("CALL VALUE", call['size'])

                total_exit_price += exit_price
                total_entry_price += call['cost'] * call['size']
        
        # Process puts
        for put in self.position['puts']:
            expiry_data = self.data[self.data['QUOTE_DATE'] == put['expiry']]
            if not expiry_data.empty:
                S = expiry_data['UNDERLYING_LAST'].values[0]  # underlying price at expiration
                K = put['strike']
                put_value = max(0, K - S)
                exit_price = put_value * put['size']
                total_exit_price += exit_price
                total_entry_price += put['cost'] * put['size']
        
        # Calculate overall P&L
        pnl = total_exit_price - total_entry_price
        self.cash += total_exit_price
        
        return pnl, self.cash

class StraddleStrategy(OptionStrategy):
    def enter_position(self):
        """Open a straddle position at the specified start date"""
        current_data = self.data.loc[self.data['QUOTE_DATE'] == self.start_date]

        if (current_data.empty):
            raise ValueError("Start date has no corresponding quotes")

        current_price = current_data['UNDERLYING_LAST'].values[0]

        call_option = self.find_closest_option('call', self.start_date, current_price, self.expiration_date)

        put_option = self.find_closest_option('put', self.start_date, current_price, self.expiration_date)
        
        single_total_cost = call_option['C_ASK'] + put_option['P_ASK'] # cost of one straddle

        position_size = math.floor(self.cash / single_total_cost) # number of straddles to buy

        self.position = {
            "calls": [
                {
                    "expiry": call_option['EXPIRE_DATE'],
                    "strike": call_option['STRIKE'],
                    "cost": call_option['C_ASK'],
                    "implied_vol": call_option['C_IV'],
                    "size": position_size,
                }
            ],
            "puts": [
                {
                    "expiry": put_option['EXPIRE_DATE'],
                    "strike": put_option['STRIKE'],
                    "cost": call_option['P_ASK'],
                    "implied_vol": put_option['P_IV'],
                    "size": position_size,
                }
            ]
        }

        self.expiration_date = call_option['EXPIRE_DATE']
        self.strike = call_option['STRIKE']
        self.cash -= position_size * single_total_cost
        self.daily_values[0] = position_size + self.cash 


def load_and_filter_data(file_path, strike_distance_pct_threshold=0.05):
    columns = [
    'QUOTE_UNIXTIME', 'QUOTE_READTIME', 'QUOTE_DATE', 'QUOTE_TIME_HOURS', 
    'UNDERLYING_LAST', 'EXPIRE_DATE', 'EXPIRE_UNIX', 'DTE', 'C_DELTA', 
    'C_GAMMA', 'C_VEGA', 'C_THETA', 'C_RHO', 'C_IV', 'C_VOLUME', 'C_LAST', 
    'C_SIZE', 'C_BID', 'C_ASK', 'STRIKE', 'P_BID', 'P_ASK', 'P_SIZE', 
    'P_LAST', 'P_DELTA', 'P_GAMMA', 'P_VEGA', 'P_THETA', 'P_RHO', 'P_IV', 
    'P_VOLUME', 'STRIKE_DISTANCE', 'STRIKE_DISTANCE_PCT']

    # Read the text file into a pandas DataFrame
    df = pd.read_csv(file_path, header=None, names=columns, dtype='unicode')

    # Convert necessary columns to appropriate data types
    df['STRIKE_DISTANCE_PCT'] = pd.to_numeric(df['STRIKE_DISTANCE_PCT'], errors='coerce')

    # Convert QUOTE_DATE and EXPIRE_DATE to datetime, STRIKE to numeric
    df['QUOTE_DATE'] = pd.to_datetime(df['QUOTE_DATE'], format=' %Y-%m-%d', errors='coerce')
    df['EXPIRE_DATE'] = pd.to_datetime(df['EXPIRE_DATE'], format=' %Y-%m-%d', errors='coerce')
    df['STRIKE'] = pd.to_numeric(df['STRIKE'], errors='coerce')
    df['UNDERLYING_LAST'] = pd.to_numeric(df['UNDERLYING_LAST'], errors='coerce')
    df['C_ASK'] = pd.to_numeric(df['C_ASK'], errors='coerce')
    df['P_ASK'] = pd.to_numeric(df['P_ASK'], errors='coerce')

    # Filter for STRIKE_DISTANCE_PCT less than the threshold
    filtered_df = df[df['STRIKE_DISTANCE_PCT'] < strike_distance_pct_threshold]

    return filtered_df

def backtest_straddle(start_date, duration, cash=10000):
    """Run backtest for the straddle strategy"""
    file_path = "spy2023/spy_eod_202301.txt"
    data = load_and_filter_data(file_path)
    
    straddle_strategy = StraddleStrategy(initial_cash=cash, data=data, start_date=start_date, duration=duration)
    straddle_strategy.enter_position()
    daily_values = straddle_strategy.reevaluate_position_daily()
    pnl, final_cash = straddle_strategy.close_position()
    
    return pnl, final_cash, daily_values

def execute_backtest(start_date, duration, cash, strategy):
    if strategy == "Straddle":
        return backtest_straddle(start_date=start_date, duration=duration, cash=cash)

def main():
    start_date = "2023-01-03"
    duration = 27

    pnl, final_cash, daily_values = backtest_straddle(start_date, duration)
    
    print(f"Straddle Strategy: Final Cash: ${final_cash:.2f}, PnL: ${pnl:.2f}")
    print(f"Daily Value Fluctuations: {daily_values}")

if __name__ == "__main__":
    main()