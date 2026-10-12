package SQ.CustomAnalysis;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.project.*;

import SQ.Columns.Trades.*;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * Write every strategy's trade list from memory, byte for byte the CSV `-tools action=orderstocsv`
 * writes: one "<strategy>.csv" per strategy, 16 quoted columns, semicolons, CRLF, main result only.
 *
 * inputArgs: "project|databank|folder" — whose strategies, and where to write. The task's own
 * databank is not read and is returned untouched, so one tool project serves every project of the
 * session. "_done.tsv" is written last, one row per strategy with its trade count: a folder
 * without it is an export that did not finish.
 *
 * Every column but the two prices is formatted by SQX's own trade-list snippet. The prices are
 * formatted here, the same expression, with the symbol's decimals looked up ONCE: SQX's OpenPrice and ClosePrice ask
 * DataManager on every row, which was 237 of the 245 s of 1,000 strategies (2026-10-12).
 */
public class AlgoTrades extends CustomAnalysisMethod {

    private static final String HEADER = "\"Ticket\";\"Symbol\";\"Type\";\"Open time\";\"Open price\";\"Size\";"
            + "\"Close time\";\"Close price\";\"Profit/Loss\";\"Balance\";\"Sample type\";\"Close type\";"
            + "\"MAE ($)\";\"MFE ($)\";\"Time in trade\";\"Comment\"";
    private static final int OPEN_PRICE = 4;
    private static final int CLOSE_PRICE = 7;

    public AlgoTrades() {
        super("AlgoTrades", TYPE_PROCESS_DATABANK);
    }

    @Override
    public boolean filterStrategy(String project, String task, String databankName, ResultsGroup rg) throws Exception {
        return true;
    }

    @Override
    public ArrayList<ResultsGroup> processDatabank(String project, String task, String databankName, ArrayList<ResultsGroup> databankRG) throws Exception {
        // "project|databank|folder": the task lives in a tool project of its own and reads another's
        String[] args = this.getInputArgs().trim().split("\\|");
        Databank source = ProjectEngine.get(args[0]).getDatabanks().get(args[1]);
        ArrayList<ResultsGroup> strategies = new ArrayList<>(source.getRecords());
        Path out = Paths.get(args[2]);
        Files.createDirectories(out);
        Files.deleteIfExists(out.resolve("_done.tsv"));
        TradelistColumn[] columns = {new Ticket(), new Symbol(), new Type(), new OpenTime(), null,
                new Size(), new CloseTime(), null, new ProfitLoss(), new Balance(), new SampleType(),
                new CloseType(), new MAE(), new MFE(), new TimeInTrade(), new Comment()};
        // symbol -> its decimals, or null when SQX does not know the symbol
        HashMap<String, Integer> decimals = new HashMap<>();
        List<String> done = new ArrayList<>();
        for (ResultsGroup rg : strategies) {
            OrdersList orders = rg.orders().filterWithClone(rg.getMainResultKey(), Directions.Both, SampleTypes.FullSample);
            int rows = 0;
            try (BufferedWriter w = Files.newBufferedWriter(out.resolve(rg.getName() + ".csv"), StandardCharsets.UTF_8)) {
                w.write(HEADER);
                w.write("\r\n");
                for (int i = 0; i < orders.size(); i++) {
                    Order order = orders.get(i);
                    if (order.isBalanceOrder()) continue;
                    if (!decimals.containsKey(order.Symbol)) {
                        DataInfo info = DataManager.getDataInfo("History", order.Symbol);
                        decimals.put(order.Symbol, info == null ? null : info.symbolInfo.decimals);
                    }
                    Integer places = decimals.get(order.Symbol);
                    StringBuilder line = new StringBuilder();
                    for (int k = 0; k < columns.length; k++) {
                        String text;
                        if (k == OPEN_PRICE) {
                            text = places == null ? order.OpenPrice + "" : SQUtils.d2String(order.OpenPrice, places);
                        } else if (k == CLOSE_PRICE) {
                            text = order.isPendingOrder() ? ""
                                    : places == null ? order.ClosePrice + "" : SQUtils.d2String(order.ClosePrice, places);
                        } else {
                            Object value = columns[k].getValue(order);
                            text = value == null ? "" : columns[k].getFormattedValue(value);
                        }
                        if (k > 0) line.append(';');
                        line.append('"').append(text == null ? "" : text).append('"');
                    }
                    w.write(line.toString());
                    w.write("\r\n");
                    rows++;
                }
            }
            done.add(rg.getName() + "\t" + rows);
        }
        Files.write(out.resolve("_done.tsv"), done, StandardCharsets.UTF_8);
        return databankRG;
    }
}
