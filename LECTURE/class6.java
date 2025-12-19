public class class6 {
    public static void main(String[] args) {
        // Nested Loops - Beginner Level
        
        // Example 1: Print a simple multiplication table
        System.out.println("=== Multiplication Table ===");
        for (int i = 1; i <= 3; i++) {
            for (int j = 1; j <= 3; j++) {
                System.out.print(i * j + "\t");
            }
            System.out.println();
        }
        
        // Example 2: Print a square pattern with asterisks
        System.out.println("\n=== Square Pattern ===");
        int size = 4;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                System.out.print("* ");
            }
            System.out.println();
        }
        
        // Example 3: Print a triangle pattern
        System.out.println("\n=== Triangle Pattern ===");
        int rows = 5;
        for (int i = 1; i <= rows; i++) {
            for (int j = 0; j < i; j++) {
                System.out.print("* ");
            }
            System.out.println();
        }
        
        // Example 4: Print a pyramid pattern
        System.out.println("\n=== Pyramid Pattern ===");
        int pyramidSize = 5;
        for (int i = 1; i <= pyramidSize; i++) {
            // Print spaces
            for (int j = pyramidSize - i; j > 0; j--) {
                System.out.print(" ");
            }
            // Print stars
            for (int j = 0; j < i; j++) {
                System.out.print("* ");
            }
            System.out.println();
        }
    }
}
