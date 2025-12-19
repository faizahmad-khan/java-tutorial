public class class7 {
    public static void main(String[] args) {
        // String Manipulation - Beginner Level
        
        String name = "Java";
        String greeting = "Welcome to Programming";
        
        // String length
        System.out.println("Length of '" + name + "': " + name.length());
        
        // Convert to uppercase and lowercase
        System.out.println("Uppercase: " + greeting.toUpperCase());
        System.out.println("Lowercase: " + greeting.toLowerCase());
        
        // Check if string contains a character/substring
        String message = "Hello World";
        System.out.println("Does message contain 'World'? " + message.contains("World"));
        
        // Get character at specific index
        System.out.println("First character: " + message.charAt(0));
        System.out.println("Last character: " + message.charAt(message.length() - 1));
        
        // String concatenation
        String firstName = "John";
        String lastName = "Doe";
        String fullName = firstName + " " + lastName;
        System.out.println("Full Name: " + fullName);
        
        // Replace characters in string
        String text = "Java is fun";
        String newText = text.replace("fun", "awesome");
        System.out.println("Original: " + text);
        System.out.println("After replace: " + newText);
        
        // Check if strings are equal
        String str1 = "Hello";
        String str2 = "Hello";
        System.out.println("Are str1 and str2 equal? " + str1.equals(str2));
        
        // Extract substring
        String word = "Programming";
        String subWord = word.substring(0, 7); // First 7 characters
        System.out.println("Substring of '" + word + "': " + subWord);
    }
}
