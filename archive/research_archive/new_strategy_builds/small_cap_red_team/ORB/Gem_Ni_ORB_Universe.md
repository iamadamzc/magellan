he strategies are designed for speedboats, but you are driving oil tankers.Momentum scalping strategies (ORB, Flags, Traps) rely on Supply/Demand Imbalance.1Low Float (< 20M): A small increase in buying exhausts the sellers $\rightarrow$ Price jumps 5% in seconds. (Physics of Scarcity).High Float (RIOT/MARA): A massive increase in buying is absorbed by millions of limit sell orders (The "Thick Book") $\rightarrow$ Price grinds up 0.5% in 10 minutes. (Physics of Liquidity).Here is the precise quantitative universe you should filter for to make your original "Fast Scalp" strategies work, versus what you need for RIOT/MARA.The "Golden Universe" (The Speedboats)Use this universe if you want to use your V5 / Original Rules (Tight stops, 5-min FTA, Fast Scaling).You need stocks where the physics favors explosive movement.MetricFilter RangeThe Physics "Why"Float< 20 MillionCrucial. Low supply means it takes less capital to move price. RIOT (200M+ float) absorbs buying; these stocks launch on it.Market Cap$50M – $500MToo big (>$1B) = Algorithmic efficiency (chop). Too small (<$20M) = Manipulation risk.Relative Vol (RVOL)> 3.0The stock must be trading 3x its normal volume. This confirms "New Eyes" are watching.Gap %> 15% (Pre-Market)Ensures a Catalyst (News/Earnings) is present. You need a reason for momentum.Price$2.00 – $15.00The Retail Sweet Spot. Over $20, retail volume fades. Under $2, spreads are mathematically toxic.The "Tanker" Universe (The Grinders)Use this universe if you want to use your V7 / New Rules (Wide stops, 15-min FTA, Trend Following).This is where you are currently testing (RIOT, MARA, AMC).MetricFilter RangeThe Physics "Why"Float> 100 Million"Thick" order books. Hard to manipulate, but slow to turn.SectorCrypto / MemeThese trade on Correlation (BTC price), not Structure. Breakouts fail if BTC is dropping.ATR %> 4.0%They must be volatile enough to pay for the spread.Volume> 10M Shares/DayInstitutional liquidity allows for massive size, but kills speed.The "Toxic" Universe (Hard Exclude)Add these filters to your code immediately. These conditions kill algorithms regardless of strategy.The "Barcoders": Stocks with 1-minute Volume < 1,000. The chart looks like dashes. Impossible to exit without 2% slippage.The "Buyouts": If Gap < 2% AND ATR < $0.05. The stock is dead. It will sit flat for 6 hours.The "Spread Traps": If (Ask - Bid) / Price > 1.0%. You start the trade down -1.0%. You cannot win mathematically.Quant Implementation: The "Regime Switch"You do not have to choose one or the other. You can build a "Regime Detector" that automatically applies V5 Rules to Speedboats and V7 Rules to Tankers.Python Logic Concept:Pythondef get_strategy_parameters(ticker_data):
    """
    Returns the correct trading parameters based on the stock's 'Mass' (Float).
    """
    float_shares = ticker_data['float_shares']
    price = ticker_data['price']
    
    # UNIVERSE A: SPEEDBOAT (Micro-Cap / Momentum)
    # Logic: Fast, Aggressive, Tight
    if float_shares < 20_000_000 and price < 20:
        return {
            'regime': 'SPEEDBOAT',
            'fta_time': 5,                  # Fast kill (momentum dies fast)
            'stop_loss_atr': 0.5,           # Tight stop (vertical moves)
            'target_r': 3.0,                # Aim for the moon
            'mgmt_trigger': 0.5,            # Breakeven early
            'strategy_mode': 'BREAKOUT'     # Buy strength
        }
    
    # UNIVERSE B: TANKER (Mid-Cap / Trend)
    # Logic: Slow, Patient, Wide
    elif float_shares > 100_000_000:
        return {
            'regime': 'TANKER',
            'fta_time': 15,                 # Slow kill (needs time to grind)
            'stop_loss_atr': 1.0,           # Wide breath (wicks hunt stops)
            'target_r': 1.5,                # Realistic target
            'mgmt_trigger': 0.8,            # Give it room
            'strategy_mode': 'PULLBACK'     # Buy weakness (VWAP)
        }
    
    # UNIVERSE C: THE TWILIGHT ZONE (Avoid)
    # Stocks between 20M and 100M often lack the benefits of either extreme.
    else:
        return None 
Strategic RecommendationFor V7 Testing (Current Phase): Since your V7 rules (No FTA/Relaxed FTA) are designed for slower stocks, continue testing on RIOT/MARA. You are finally matching the strategy to the asset.For Future Alpha: If you want 100%+ returns, you must eventually switch to Universe A (Speedboats). That is where the inefficiency lives. When you do, re-enable your V5 logic (Tight stops, 5-min FTA) but only for those specific stocks.