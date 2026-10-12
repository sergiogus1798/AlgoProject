package SQ.Blocks.RandomEntry;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

/**
 * A random entry that reproduces: true on a bar when a hash of (the bar's time, Seed) falls under
 * Probability. Two backtests of one strategy give the same trades; another Seed gives another
 * draw. The vendor's «(RAND) Random Entry» draws Math.random() and never repeats.
 */
@BuildingBlock(name="(RAND) Seeded Random Entry", display="Seeded Random Entry (#Probability#%, seed #Seed#)", returnType = ReturnTypes.Boolean)
@Help("Random entry signal with the given probability per bar, fixed by Seed: the same Seed always picks the same bars.")
public class SeededRandomEntry extends ConditionBlock {

    @Parameter(name="Probability", defaultValue="5", minValue=0.01, maxValue=100, step=0.01)
    public double Probability;

    @Parameter(name="Seed", defaultValue="1", minValue=0, maxValue=1000000, step=1)
    public int Seed;

    @Override
    public boolean OnBlockEvaluate() throws TradingException {
        // SplitMix64 of the bar time offset by the seed: uniform in [0, 100)
        long z = Strategy.Time(0) + 0x9E3779B97F4A7C15L * (Seed + 1L);
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        z ^= z >>> 31;
        return (z >>> 11) * 0x1.0p-53 * 100 < Probability;
    }
}
