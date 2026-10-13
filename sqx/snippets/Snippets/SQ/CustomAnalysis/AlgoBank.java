package SQ.CustomAnalysis;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.tradinglib.*;
import com.strategyquant.tradinglib.project.*;
import com.strategyquant.tradinglib.results.SpecialValues;

import SQ.Columns.Trades.*;

import it.unimi.dsi.fastutil.longs.Long2FloatMap;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.CRC32;

/**
 * Write whole databanks from memory, one binary "<databank>.abk" each: every order, the daily
 * equity and the statistics of every result, the strategy XML and an index.
 *
 * THE FORMAT IS NOT DESCRIBED HERE: it is version 1 of the module docstring of core/bankfile.py,
 * the reader. That text is the spec; this file and the writer in tests/test_perf66_algobank.py
 * follow it, and a change starts there.
 *
 * inputArgs: "project|bank1;bank2|folder|keysFile|main or all|samples" — whose databanks, where to
 * write (the caller gives /dev/shm/algobank/<role>/<project>: per install, never hardcoded here), a text file with one "name<TAB>type" per statistic to store, whether the orders are the
 * main result's or every result's, and the sample-type codes to ask statistics for ("10,11,20").
 * The task's own databank is not read and is returned untouched, as in AlgoTrades.
 *
 * A file gets its name only when it is whole: it is written as "<databank>.abk.tmp" and renamed.
 * An order whose type, sample type or close type has no label raises, and that databank gets no
 * file at all. "_done.tsv" is written last, one row per databank: name, strategies, orders, and
 * the milliseconds of the four passes (orders, equity, statistics, XML).
 *
 * One thread: parallelStream was 3.6 times slower in AlgoTrades. The order fields are written
 * WITHOUT casts on purpose: a field that is not the type the format says does not compile, and
 * the compile error names it — change the format, never add the cast.
 */
public class AlgoBank extends CustomAnalysisMethod {

    private static final int VERSION = 1;
    private static final int SECTIONS = 10;
    private static final int TRAILER = 204;
    private static final long DAY = 86400000L;
    private static final String XML_HEAD = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n";

    private FileChannel channel;
    private ByteBuffer buffer;
    private CRC32 crc;
    private long written;
    private long[][] sections;
    private LinkedHashMap<String, Integer> labels;
    private LinkedHashMap<String, Integer> strings;

    public AlgoBank() {
        super("AlgoBank", TYPE_PROCESS_DATABANK);
    }

    @Override
    public boolean filterStrategy(String project, String task, String databankName, ResultsGroup rg) throws Exception {
        return true;
    }

    @Override
    public ArrayList<ResultsGroup> processDatabank(String project, String task, String databankName, ArrayList<ResultsGroup> databankRG) throws Exception {
        String[] args = this.getInputArgs().trim().split("\\|");
        Path out = Paths.get(args[2]);
        List<String> keys = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        boolean all = args[4].equals("all");
        String[] codes = args[5].split(",");
        byte[] samples = new byte[codes.length];
        for (int i = 0; i < codes.length; i++) {
            samples[i] = Byte.parseByte(codes[i].trim());
        }
        Files.createDirectories(out);
        Files.deleteIfExists(out.resolve("_done.tsv"));
        List<String> done = new ArrayList<>();
        for (String bank : args[1].split(";")) {
            Databank source = ProjectEngine.get(args[0]).getDatabanks().get(bank);
            // a copy of the list: the databank may gain or lose strategies while this runs
            ArrayList<ResultsGroup> strategies = new ArrayList<>(source.getRecords());
            done.add(bank + "\t" + write(strategies, out.resolve(bank + ".abk"), keys, all, samples));
        }
        Files.write(out.resolve("_done.tsv"), done, StandardCharsets.UTF_8);
        return databankRG;
    }

    /** One databank to `out`; returns "strategies<TAB>orders<TAB>ms orders<TAB>equity<TAB>statistics<TAB>XML". */
    private String write(List<ResultsGroup> strategies, Path out, List<String> keys, boolean all, byte[] samples) throws Exception {
        Path tmp = out.resolveSibling(out.getFileName() + ".tmp");
        // a run that fails must not leave the previous run's file under the final name
        Files.deleteIfExists(out);
        channel = FileChannel.open(tmp, StandardOpenOption.CREATE, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING);
        try {
            String told = fill(strategies, keys, all, samples);
            channel.close();
            Files.move(tmp, out, StandardCopyOption.ATOMIC_MOVE);
            return told;
        } finally {
            channel.close();
            Files.deleteIfExists(tmp);
        }
    }

    private String fill(List<ResultsGroup> strategies, List<String> keys, boolean all, byte[] samples) throws Exception {
        buffer = ByteBuffer.allocateDirect(1 << 20).order(ByteOrder.LITTLE_ENDIAN);
        crc = new CRC32();
        written = 0;
        sections = new long[SECTIONS][2];
        labels = new LinkedHashMap<>();
        strings = new LinkedHashMap<>();
        id(labels, "");
        id(strings, "");
        int n = strategies.size();
        int k = keys.size();
        String[] names = new String[k];
        for (int i = 0; i < k; i++) {
            names[i] = keys.get(i).split("\t")[0];
        }
        int[] orderCount = new int[n];
        int[] xmlLength = new int[n];
        long orderTotal = 0;
        // symbol -> its decimals, -1 when SQX does not know the symbol; looked up once, as AlgoTrades
        LinkedHashMap<String, Integer> decimals = new LinkedHashMap<>();
        ArrayList<int[]> runs = new ArrayList<>();
        Type type = new Type();
        SampleType sample = new SampleType();
        CloseType close = new CloseType();
        long[] clock = new long[5];

        buffer.put("ALGOBANK".getBytes(StandardCharsets.US_ASCII)).putInt(VERSION).putInt(all ? 1 : 0);

        clock[0] = System.nanoTime();
        begin(0);                                                   // orders
        for (int s = 0; s < n; s++) {
            ResultsGroup rg = strategies.get(s);
            OrdersList orders = all ? rg.orders()
                    : rg.orders().filterWithClone(rg.getMainResultKey(), Directions.Both, SampleTypes.FullSample);
            for (int i = 0; i < orders.size(); i++) {
                Order order = orders.get(i);
                if (order.isBalanceOrder()) continue;
                if (!decimals.containsKey(order.Symbol)) {
                    DataInfo info = DataManager.getDataInfo("History", order.Symbol);
                    decimals.put(order.Symbol, info == null ? -1 : info.symbolInfo.decimals);
                }
                int symbolId = id(labels, order.Symbol);
                int resultId = id(labels, order.SetupName);
                int typeId = label(type.getFormattedValue(type.getValue(order)), "type", rg);
                int sampleId = label(sample.getFormattedValue(sample.getValue(order)), "sample type", rg);
                int closeId = label(close.getFormattedValue(close.getValue(order)), "close type", rg);
                room(64);
                // no casts: see the class comment. MAE with the trade list's sign (SQ.Columns.Trades.MAE)
                buffer.putInt(s).putInt(order.Ticket).putLong(order.OpenTime).putLong(order.CloseTime)
                        .putFloat(order.OpenPrice).putFloat(order.ClosePrice).putFloat(order.Size)
                        .putFloat(order.PL).putFloat(order.AccountBalance)
                        .putFloat(order.MAE == 0 ? order.MAE : -1 * order.MAE).putFloat(order.MFE)
                        .putShort((short) symbolId).putShort((short) resultId).putShort((short) typeId)
                        .putShort((short) sampleId).putShort((short) closeId)
                        .put((byte) (order.isPendingOrder() ? 1 : 0)).put((byte) 0);
                orderCount[s]++;
                orderTotal++;
            }
            if (labels.size() > 65535) {
                throw new Exception("AlgoBank: more than 65535 order labels at " + rg.getName());
            }
        }

        clock[1] = System.nanoTime();
        begin(1);                                                   // equity
        for (int s = 0; s < n; s++) {
            ResultsGroup rg = strategies.get(s);
            for (String key : rg.getResultKeys()) {
                Long2FloatRBTreeMap equity = rg.subResult(key).getWorstDailyEquity();
                if (equity == null || equity.isEmpty()) continue;
                int points = 0;
                for (Long2FloatMap.Entry point : equity.long2FloatEntrySet()) {
                    room(8);
                    buffer.putInt((int) Math.floorDiv(point.getLongKey(), DAY)).putFloat(point.getFloatValue());
                    points++;
                }
                runs.add(new int[]{s, id(strings, key), points});
            }
        }

        clock[2] = System.nanoTime();
        begin(2);                                                   // stats
        for (int s = 0; s < n; s++) {
            ResultsGroup rg = strategies.get(s);
            for (String key : rg.getResultKeys()) {
                for (byte code : samples) {
                    SQStats stats;
                    try {
                        stats = rg.subResult(key).stats(Directions.Both, PlTypes.Money, code);
                    } catch (StatsDontExistException absent) {
                        // a sample this result was never computed for: SQX throws, it does not return
                        // null (2026-10-13). Never computeAllStats() here: that would change the databank.
                        continue;
                    }
                    if (stats == null) continue;
                    room(12 + 8 * k);
                    buffer.putInt(s).putInt(id(strings, key)).put(code).put((byte) 0).put((byte) 0).put((byte) 0);
                    for (String name : names) {
                        // NaN for a key this block does not carry: without the default SQX answers 0
                        buffer.putDouble(stats.getDouble(name, Double.NaN));
                    }
                }
            }
        }

        clock[3] = System.nanoTime();
        begin(3);                                                   // xml
        for (int s = 0; s < n; s++) {
            // the element as text is the .sqx member strategy_Portfolio.xml without its first line and
            // its last line break (100 of 100 strategies, 2026-10-13): put both back, byte for byte
            byte[] xml = (XML_HEAD + XMLUtil.elementToString(strategies.get(s).getStrategyXml()) + "\r\n")
                    .getBytes(StandardCharsets.UTF_8);
            xmlLength[s] = xml.length;
            bytes(xml);
        }

        clock[4] = System.nanoTime();
        begin(4);                                                   // index
        for (int s = 0; s < n; s++) {
            ResultsGroup rg = strategies.get(s);
            SettingsMap special = rg.specialValues();
            int filter = special.containsKey(SpecialValues.FiltersResultFailedReason)
                    ? id(strings, special.getString(SpecialValues.FiltersResultFailedReason)) : 0;
            room(32);
            buffer.putInt(id(strings, rg.getName())).putInt(id(strings, rg.getMainResultKey()))
                    .putInt(id(strings, special.getString(SpecialValues.Symbol, "")))
                    .putInt(id(strings, special.getString(SpecialValues.Timeframe, "")))
                    .putInt(filter).putInt(special.getInt(SettingsKeys.StrategyProblems, 0))
                    .putInt(orderCount[s]).putInt(xmlLength[s]);
        }
        begin(5);                                                   // eqruns
        for (int[] run : runs) {
            room(12);
            buffer.putInt(run[0]).putInt(run[1]).putInt(run[2]);
        }
        begin(6);                                                   // symdec
        for (Map.Entry<String, Integer> symbol : decimals.entrySet()) {
            room(8);
            buffer.putInt(id(labels, symbol.getKey())).putInt(symbol.getValue());
        }
        begin(7);                                                   // keys
        for (String key : keys) {
            room(4);
            buffer.putInt(id(strings, key));
        }
        begin(8);                                                   // labels
        table(labels);
        begin(9);                                                   // strings
        table(strings);
        begin(SECTIONS);

        // the trailer; the CRC covers every byte before itself
        room(TRAILER);
        long size = written + buffer.position() + TRAILER;
        for (long[] section : sections) {
            buffer.putLong(section[0]).putLong(section[1]);
        }
        buffer.putInt(n).putInt(k).putLong(orderTotal).putLong(System.currentTimeMillis()).putLong(size);
        flush();
        buffer.putInt((int) crc.getValue()).put("KNABOGLA".getBytes(StandardCharsets.US_ASCII));
        flush();
        if (written != size) {
            throw new Exception("AlgoBank: wrote " + written + " bytes and the trailer says " + size);
        }
        StringBuilder told = new StringBuilder().append(n).append('\t').append(orderTotal);
        for (int i = 0; i < 4; i++) {
            told.append('\t').append((clock[i + 1] - clock[i]) / 1000000L);
        }
        return told.toString();
    }

    /** The id of a string in one of the two tables, given in order of first use. */
    private int id(Map<String, Integer> table, String text) {
        String key = text == null ? "" : text;
        Integer at = table.get(key);
        if (at == null) {
            at = table.size();
            table.put(key, at);
        }
        return at;
    }

    /** The label id of an order's type, sample type or close type; none, and the databank gets no file. */
    private int label(String text, String what, ResultsGroup rg) throws Exception {
        if (text == null || text.isEmpty() || text.equals("N/A")) {
            throw new Exception("AlgoBank: " + rg.getName() + " has an order whose " + what + " has no label");
        }
        return id(labels, text);
    }

    private void room(int bytes) throws Exception {
        if (buffer.remaining() < bytes) flush();
    }

    private void flush() throws Exception {
        buffer.flip();
        crc.update(buffer.duplicate());
        written += buffer.remaining();
        while (buffer.hasRemaining()) {
            channel.write(buffer);
        }
        buffer.clear();
    }

    /** Close the section before `section` and open it; SECTIONS closes the last. */
    private void begin(int section) {
        long at = written + buffer.position();
        if (section > 0) sections[section - 1][1] = at - sections[section - 1][0];
        if (section < SECTIONS) sections[section][0] = at;
    }

    private void bytes(byte[] data) throws Exception {
        int at = 0;
        while (at < data.length) {
            if (!buffer.hasRemaining()) flush();
            int step = Math.min(buffer.remaining(), data.length - at);
            buffer.put(data, at, step);
            at += step;
        }
    }

    /** A string table: count, offsets[count + 1], then the UTF-8 bytes. */
    private void table(Map<String, Integer> table) throws Exception {
        ArrayList<byte[]> texts = new ArrayList<>();
        room(4);
        buffer.putInt(table.size());
        int at = 0;
        for (String text : table.keySet()) {
            byte[] data = text.getBytes(StandardCharsets.UTF_8);
            texts.add(data);
            room(4);
            buffer.putInt(at);
            at += data.length;
        }
        room(4);
        buffer.putInt(at);
        for (byte[] data : texts) {
            bytes(data);
        }
    }
}
