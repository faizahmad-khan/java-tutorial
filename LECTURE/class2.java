public class class2 {
    public static void main(String[] args) {
        int a = 10;
        int b = 20;
        int c = 30;
        int largest = a;

        if (b > largest) {
            largest = b;
        }
        if (c > largest) {
            largest = c;
        }

        System.out.println("Largest number is: " + largest);
    }   
}
