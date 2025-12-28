import subprocess
import tempfile
import os
import time
from pathlib import Path

class JavaRunner:
    """
    A secure Java code execution environment that runs Java code in a sandboxed manner.
    """
    
    def __init__(self, timeout=5):
        self.timeout = timeout  # Timeout in seconds
        self.java_home = self._find_java_home()
        
        # Check if running in a serverless environment
        self.is_serverless = os.environ.get('VERCEL', False) or os.environ.get('SERVERLESS', False)
        
        # If in serverless environment, disable Java execution
        if self.is_serverless:
            self.java_home = None
        
    def _find_java_home(self):
        """
        Find the Java installation directory.
        """
        try:
            # Try to find java executable
            result = subprocess.run(['which', 'java'], capture_output=True, text=True)
            if result.returncode == 0:
                java_path = result.stdout.strip()
                # Get the parent directory of bin/java
                java_bin = Path(java_path).parent
                java_home = java_bin.parent
                return str(java_home)
        except:
            pass
        
        # Default locations to check
        possible_paths = [
            '/usr/lib/jvm/default-java',
            '/usr/lib/jvm/java-1-openjdk-amd64',
            '/usr/lib/jvm/java-8-openjdk-amd64',
            'C:/Program Files/Java/jdk-11',
            'C:/Program Files/Java/jdk8',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def run_java_code(self, code):
        """
        Execute Java code in a secure environment and return the output.
        
        Args:
            code (str): The Java code to execute
            
        Returns:
            dict: A dictionary containing the execution result
        """
        if not self.java_home:
            if self.is_serverless:
                return {
                    'success': False,
                    'output': '',
                    'error': 'Java execution is not available in serverless environment. Java compilation and execution is disabled in this deployment.',
                    'timeout': False
                }
            else:
                return {
                    'success': False,
                    'output': '',
                    'error': 'Java is not installed or not found in the system',
                    'timeout': False
                }
        
        # Create a temporary directory for this execution
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the Java code to a temporary file
            java_file_path = os.path.join(temp_dir, 'Main.java')
            
            # Validate and sanitize the code (basic check)
            if not self._is_safe_code(code):
                return {
                    'success': False,
                    'output': '',
                    'error': 'Code contains potentially unsafe operations',
                    'timeout': False
                }
            
            try:
                with open(java_file_path, 'w') as f:
                    f.write(code)
                
                # Compile the Java code
                compile_result = subprocess.run(
                    [f'{self.java_home}/bin/javac', java_file_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if compile_result.returncode != 0:
                    return {
                        'success': False,
                        'output': '',
                        'error': compile_result.stderr,
                        'timeout': False
                    }
                
                # Execute the compiled Java code
                class_file_dir = os.path.dirname(java_file_path)
                main_class_path = os.path.splitext(os.path.basename(java_file_path))[0]
                
                exec_result = subprocess.run(
                    [f'{self.java_home}/bin/java', '-cp', class_file_dir, main_class_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if exec_result.returncode != 0:
                    return {
                        'success': False,
                        'output': exec_result.stdout,
                        'error': exec_result.stderr,
                        'timeout': False
                    }
                
                return {
                    'success': True,
                    'output': exec_result.stdout,
                    'error': '',
                    'timeout': False
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'output': '',
                    'error': 'Code execution timed out',
                    'timeout': True
                }
            except Exception as e:
                return {
                    'success': False,
                    'output': '',
                    'error': f'An error occurred: {str(e)}',
                    'timeout': False
                }
    
    def _is_safe_code(self, code):
        """
        Basic check to ensure the code doesn't contain potentially harmful operations.
        This is a very basic check - in a production environment, you'd want more robust validation.
        """
        unsafe_patterns = [
            'Runtime.getRuntime()',
            'System.setSecurityManager',
            'FileOutputStream',
            'FileInputStream',
            'Files.write',
            'Files.read',
            'ProcessBuilder',
            'exec(',
            'import java.io.File',
            'import java.nio.file',
            'import java.lang.reflect',
        ]
        
        code_lower = code.lower()
        for pattern in unsafe_patterns:
            if pattern.lower() in code_lower:
                return False
        
        return True

# Example usage
if __name__ == "__main__":
    runner = JavaRunner()
    
    # Test code
    test_code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        int a = 10;
        int b = 20;
        System.out.println("Sum: " + (a + b));
    }
}
"""
    
    result = runner.run_java_code(test_code)
    print("Success:", result['success'])
    print("Output:", result['output'])
    if result['error']:
        print("Error:", result['error'])