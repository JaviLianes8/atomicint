// Reference answers from the Java runtime for the atomicint oracle tests.
//
// Reads one command per line on stdin and prints one result per line:
//   new V | get | set V | addAndGet V | getAndAdd V | incrementAndGet | decrementAndGet
//   getAndSet V | compareAndSet E V | compareAndExchange E V
//   updateAndGet F | getAndUpdate F        (F: double, negate, plus7, halve)
// act on one java.util.concurrent.atomic.AtomicLong;
//   clamp V LO HI        Math.clamp(long, long, long)
//   wrap8|wrap16|wrap32 V, uwrap8|uwrap16|uwrap32 V   Java narrowing conversions
//   add64 A B            long addition, which wraps around at 64 bits
// Run with: java scripts/oracle/AtomicOracle.java < commands.txt
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.LongUnaryOperator;

public class AtomicOracle {
    static LongUnaryOperator function(String name) {
        switch (name) {
            case "double": return x -> x * 2;
            case "negate": return x -> -x;
            case "plus7": return x -> x + 7;
            case "halve": return x -> Math.floorDiv(x, 2L);
            default: throw new IllegalArgumentException(name);
        }
    }

    static String run(AtomicLong[] cell, String[] p) {
        AtomicLong a = cell[0];
        switch (p[0]) {
            case "new": cell[0] = new AtomicLong(Long.parseLong(p[1])); return Long.toString(cell[0].get());
            case "get": return Long.toString(a.get());
            case "set": a.set(Long.parseLong(p[1])); return Long.toString(a.get());
            case "addAndGet": return Long.toString(a.addAndGet(Long.parseLong(p[1])));
            case "getAndAdd": return Long.toString(a.getAndAdd(Long.parseLong(p[1])));
            case "incrementAndGet": return Long.toString(a.incrementAndGet());
            case "decrementAndGet": return Long.toString(a.decrementAndGet());
            case "getAndSet": return Long.toString(a.getAndSet(Long.parseLong(p[1])));
            case "compareAndSet":
                return Boolean.toString(a.compareAndSet(Long.parseLong(p[1]), Long.parseLong(p[2])));
            case "compareAndExchange":
                return Long.toString(a.compareAndExchange(Long.parseLong(p[1]), Long.parseLong(p[2])));
            case "updateAndGet": return Long.toString(a.updateAndGet(function(p[1])));
            case "getAndUpdate": return Long.toString(a.getAndUpdate(function(p[1])));
            case "clamp":
                return Long.toString(Math.clamp(Long.parseLong(p[1]), Long.parseLong(p[2]), Long.parseLong(p[3])));
            case "wrap8": return Byte.toString((byte) Long.parseLong(p[1]));
            case "wrap16": return Short.toString((short) Long.parseLong(p[1]));
            case "wrap32": return Integer.toString((int) Long.parseLong(p[1]));
            case "uwrap8": return Integer.toString(Byte.toUnsignedInt((byte) Long.parseLong(p[1])));
            case "uwrap16": return Integer.toString((char) Long.parseLong(p[1]));
            case "uwrap32": return Long.toString(Integer.toUnsignedLong((int) Long.parseLong(p[1])));
            case "add64": return Long.toString(Long.parseLong(p[1]) + Long.parseLong(p[2]));
            default: throw new IllegalArgumentException(p[0]);
        }
    }

    public static void main(String[] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        StringBuilder out = new StringBuilder();
        AtomicLong[] cell = {new AtomicLong()};
        for (String line; (line = in.readLine()) != null; ) {
            if (!line.isBlank()) out.append(run(cell, line.trim().split(" "))).append('\n');
        }
        System.out.print(out);
    }
}
