public class class8 {

    public static void main(String[] args) {
        // Calling methods
        greetUser("Alice");
        int sum = addNumbers(10, 20);
        System.out.println("Sum: " + sum);
        
        // Overloaded method calls
        printMessage("This is a message.");
        printMessage("Hello", 5);
    }

    // Method without return value and with one parameter
    public static void greetUser(String name) {
        System.out.println("Hello, " + name + "!");
    }

    // Method with return value and two parameters
    public static int addNumbers(int a, int b) {
        return a + b;
    }

    // Method overloading: Same name, different parameters
    public static void printMessage(String message) {
        System.out.println(message);
    }

    public static void printMessage(String message, int count) {
        for (int i = 0; i < count; i++) {
            System.out.println(message);
        }
    }

    // Method to demonstrate scope (local variable)
    public static void demonstrateScope() {
        int localVar = 100; // This variable is local to demonstrateScope method
        System.out.println("Inside demonstrateScope: " + localVar);
    }
}
