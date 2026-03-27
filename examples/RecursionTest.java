public class RecursionTest {
    public static int test(int n) {
        if (n <= 0) {
            return 0;
        }
        return n + test(n - 2);
    }

    public static void main(String[] args) {
        System.out.println("test(5) = " + test(5));
        System.out.println("test(6) = " + test(6));
        System.out.println("test(4) = " + test(4));
        System.out.println("test(0) = " + test(0));
        System.out.println("test(-1) = " + test(-1));
    }
}