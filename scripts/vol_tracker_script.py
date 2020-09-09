from decimal import Decimal
from hummingbot.script.script_base import ScriptBase

s_decimal_1 = Decimal("1")

# modified from SpreadsAdjustedOnVolatility, spreads_adjusted_on_volatility_script.py
class VolTracker(ScriptBase):
    """
    Tracks and display vols on running strat, might use to modify param next
    The volatility, in this example, is simply a price change compared to the previous cycle regardless of its
    direction, e.g. if price changes -3% (or 3%), the volatility is 3%.
    To update our pure market making spreads, we're gonna smooth out the volatility by averaging it over a short period
    (short_period), and we need a benchmark to compare its value against. In this example the benchmark is a median
    long period price volatility (you can also use a fixed number, e.g. 3% - if you expect this to be the norm for your
    market).
    """

    # Let's set interval and sample sizes as below.
    # These numbers are for testing purposes only (in reality, they should be larger numbers)
    interval = 2        # 2 secs interval
    short_period = 15   # 15 * 2 secs, 30 secs elapsed
    long_period = 30 #1mins for now # 600   # 20 mins

    prev_vol = None

    def __init__(self):
        super().__init__()
        self.original_bid_spread = None
        self.original_ask_spread = None

    def on_tick(self):
        # First, let's keep the original spreads.
        if self.original_bid_spread is None:
            self.original_bid_spread = self.pmm_parameters.bid_spread
            self.original_ask_spread = self.pmm_parameters.ask_spread

        # Average volatility (price change) over a short period of time, this is to detect recent sudden changes.
        avg_short_volatility = self.avg_price_volatility(self.interval, self.short_period)
        # Median volatility over a long period of time, this is to find the market norm volatility.
        # We use median (instead of average) to find the middle volatility value - this is to avoid recent
        # spike affecting the average value.
        median_long_volatility = self.median_price_volatility(self.interval, self.long_period)

        # If the bot just got started, we'll not have these numbers yet as there is not enough mid_price sample size.
        # We'll start to have these numbers after interval * long_term_period (150 seconds in this example).

        #self.log(f"avg_short_volatility: {avg_short_volatility} prev_vol={self.prev_vol}")
        if self.prev_vol is None or abs(avg_short_volatility - self.prev_vol) < 0.0002 :
            return

        self.prev_vol=avg_short_volatility

        if avg_short_volatility is None or median_long_volatility is None:
            self.log(f"avg_short_volatility: {avg_short_volatility} median_long_volatility: {median_long_volatility}")
            return

        # This volatility delta will be used to adjust spreads.
        delta = avg_short_volatility - median_long_volatility
        # Let's round the delta into 0.25% increment to ignore noise and to avoid adjusting the spreads too often.
        spread_adjustment = self.round_by_step(delta, Decimal("0.0025"))
        # Show the user on what's going, you can remove this statement to stop the notification.
        self.log(f"avg_short_volatility: {avg_short_volatility} median_long_volatility: {median_long_volatility} "
                    f"spread_adjustment: {spread_adjustment}")

        #new_bid_spread = self.original_bid_spread + spread_adjustment
        # Let's not set the spreads below the originals, this is to avoid having spreads to be too close
        # to the mid price.
        #self.pmm_parameters.bid_spread = max(self.original_bid_spread, new_bid_spread)
        #new_ask_spread = self.original_ask_spread + spread_adjustment
        #self.pmm_parameters.ask_spread = max(self.original_ask_spread, new_ask_spread)
