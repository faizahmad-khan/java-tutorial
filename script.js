// Java Learning Platform - Interactive Components

// DOM Elements
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
const runCodeBtn = document.getElementById('run-code');
const resetCodeBtn = document.getElementById('reset-code');
const submitAnswerBtn = document.getElementById('submit-answer');
const outputDiv = document.getElementById('output');
const quizForm = document.getElementById('quiz-form');
const prevLessonBtn = document.getElementById('prev-lesson');
const nextLessonBtn = document.getElementById('next-lesson');

// Initialize Ace Editor
let editor;
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the Ace editor
    editor = ace.edit("editor", {
        maxLines: 30,
        theme: "ace/theme/clouds"
    });
    
    // Set Java mode
    editor.session.setMode("ace/mode/java");
    
    // Set initial content to empty
    editor.setValue("", -1); // -1 moves cursor to the start
    
    // Add syntax validation
    editor.getSession().on('changeAnnotation', function() {
        const annotations = editor.getSession().getAnnotations();
        if (annotations.length > 0) {
            console.log('Syntax errors found:', annotations);
        }
    });
    
    // Mobile menu toggle
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // Close mobile menu when clicking a link
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });

    // Run code button event
    runCodeBtn.addEventListener('click', runJavaCode);

    // Reset code button event
    resetCodeBtn.addEventListener('click', resetCode);

    // Submit answer button event
    quizForm.addEventListener('submit', checkQuizAnswers);

    // Navigation buttons
    prevLessonBtn.addEventListener('click', goToPrevLesson);
    nextLessonBtn.addEventListener('click', goToNextLesson);

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 70,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialize with first lesson
    loadLesson(1);
});

// Function to open help modal
function openHelp() {
    document.getElementById('help-modal').style.display = 'block';
    document.getElementById('help-modal').classList.add('show');
}

// Function to close help modal
function closeHelp() {
    document.getElementById('help-modal').style.display = 'none';
    document.getElementById('help-modal').classList.remove('show');
}

// Function to insert code snippet into editor
function insertSnippet(snippet) {
    if (typeof editor !== 'undefined') {
        const cursorPosition = editor.getCursorPosition();
        editor.session.insert(cursorPosition, snippet);
    } else {
        console.log("Editor not initialized");
    }
    closeHelp();
}

// Function to show specific help topic
function showHelpTopic(topicId) {
    // Hide all content sections
    document.querySelectorAll('.help-content').forEach(div => {
        div.style.display = 'none';
    });
    
    // Show the selected content
    document.getElementById(topicId + '-content').style.display = 'block';
    
    // Update active state of menu items
    document.querySelectorAll('.help-menu li').forEach(li => {
        li.classList.remove('active');
    });
    
    // Find the clicked element and make it active
    const clickedElement = event.target.tagName === 'LI' ? event.target : event.target.parentElement;
    clickedElement.classList.add('active');
}

// Function to toggle mobile menu
function toggleMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (!hamburger.contains(event.target) && !navMenu.contains(event.target)) {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    }
});

// Add event listener for help menu items
document.addEventListener('DOMContentLoaded', function() {
    // Add click event to all help menu items
    const helpMenuItems = document.querySelectorAll('.help-menu li');
    helpMenuItems.forEach(item => {
        item.addEventListener('click', function() {
            const topicId = this.getAttribute('data-topic');
            if (topicId) {
                showHelpTopic(topicId);
            }
        });
    });
    
    // Add close button functionality
    const closeButtons = document.querySelectorAll('.close-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', closeHelp);
    });
    
    // Add click outside to close modal
    const modal = document.getElementById('help-modal');
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeHelp();
        }
    });
});

// Function to run Java code
async function runJavaCode() {
    outputDiv.textContent = "Compiling and running code...\n";
    
    // Get the code from the editor
    const code = editor.getValue();
    
    try {
        const response = await fetch('/api/run_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: code })
        });
        
        const result = await response.json();
        
        if (result.success) {
            outputDiv.textContent = result.output || 'Program executed successfully with no output.';
        } else {
            outputDiv.textContent = `Error: ${result.error}`;
        }
    } catch (error) {
        outputDiv.textContent = `Error: ${error.message}`;
    }
}

// Function to reset the code to default
function resetCode() {
    if (confirm('Are you sure you want to reset the code to its original state?')) {
        // Default code for the current lesson
        const defaultCode = `public class Main {
    public static void main(String[] args) {
        // Declare and initialize variables
        int physics = 30;
        int chemistry = 20;
        int biology = 40;
        
        // Calculate total and percentage
        int total = physics + chemistry + biology;
        double percentage = (total / 300.0) * 100;
        
        System.out.println("Total marks: " + total);
        System.out.println("Percentage: " + percentage + "%");
    }
}`;
        editor.setValue(defaultCode, -1); // -1 means move cursor to the start
    }
}

// Function to check quiz answers
function checkQuizAnswers(e) {
    e.preventDefault();
    
    const q1 = document.querySelector('input[name="q1"]:checked');
    const q2 = document.querySelector('input[name="q2"]:checked');
    
    if (!q1 || !q2) {
        alert('Please answer all questions before submitting.');
        return;
    }
    
    // Correct answers (for demonstration)
    const correctQ1 = 'B'; // int number = 5;
    const correctQ2 = 'C'; // 10 12
    
    let score = 0;
    let feedback = '';
    
    if (q1.value === correctQ1) {
        score++;
        feedback += 'Question 1: Correct! ';
    } else {
        feedback += 'Question 1: Incorrect. The correct answer is B. ';
    }
    
    if (q2.value === correctQ2) {
        score++;
        feedback += 'Question 2: Correct!';
    } else {
        feedback += 'Question 2: Incorrect. The correct answer is C.';
    }
    
    alert(`${feedback}\nScore: ${score}/2`);
    
    // In a real application, we would send this to the backend to save progress
    saveProgress(score);
}

// Function to save progress
function saveProgress(score) {
    // Simulate saving progress to local storage
    // In a real application, this would send data to a backend API
    const currentProgress = JSON.parse(localStorage.getItem('javaLearningProgress') || '{}');
    
    // Update progress for current lesson
    currentProgress.currentLesson = currentProgress.currentLesson || 1;
    currentProgress[`lesson_${currentProgress.currentLesson}_score`] = score;
    
    localStorage.setItem('javaLearningProgress', JSON.stringify(currentProgress));
    
    // Update UI to reflect progress
    updateProgressUI();
}

// Function to update progress UI
function updateProgressUI() {
    // In a real application, this would update the dashboard with actual progress data
    console.log('Progress saved and UI updated');
}

// Function to navigate to previous lesson
function goToPrevLesson() {
    const currentLesson = parseInt(document.querySelector('.lesson-title').textContent.match(/\d+/)[0]);
    if (currentLesson > 1) {
        loadLesson(currentLesson - 1);
    }
}

// Function to navigate to next lesson
function goToNextLesson() {
    const currentLesson = parseInt(document.querySelector('.lesson-title').textContent.match(/\d+/)[0]);
    loadLesson(currentLesson + 1);
}

// Function to load a specific lesson
function loadLesson(lessonNumber) {
    // Update lesson title
    document.querySelector('.lesson-title').textContent = `Lesson ${lessonNumber}: Introduction to Variables`;
    
    // Update lesson content based on lesson number
    let lessonContent = '';
    let lessonCode = '';
    
    switch(lessonNumber) {
        case 1:
            lessonContent = `
                <h3>Concept Explanation</h3>
                <p>A variable is a container that holds a value which can change during program execution. In Java, variables must be declared with a specific data type before they can be used.</p>
                
                <pre><code>// Syntax: dataType variableName = value;
int age = 25;
double price = 19.99;
String name = "John";</code></pre>
                
                <h4>Try it Yourself:</h4>
                <p>Modify the code in the editor below and click "Run Code" to see the output.</p>
            `;
            lessonCode = `public class Main {
    public static void main(String[] args) {
        // Declare and initialize variables
        int physics = 30;
        int chemistry = 20;
        int biology = 40;
        
        // Calculate total and percentage
        int total = physics + chemistry + biology;
        double percentage = (total / 300.0) * 100;
        
        System.out.println("Total marks: " + total);
        System.out.println("Percentage: " + percentage + "%");
    }
}`;
            break;
        case 2:
            lessonContent = `
                <h3>Concept Explanation</h3>
                <p>Conditional statements allow your program to make decisions. The 'if-else' statement executes different blocks of code based on whether a condition is true or false.</p>
                
                <pre><code>// Syntax:
if (condition) {
    // code to execute if condition is true
} else {
    // code to execute if condition is false
}</code></pre>
                
                <h4>Try it Yourself:</h4>
                <p>Modify the code to compare different numbers.</p>
            `;
            lessonCode = `public class Main {
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
}`;
            break;
        case 3:
            lessonContent = `
                <h3>Concept Explanation</h3>
                <p>Loops allow you to execute a block of code repeatedly. The 'for' loop is commonly used when you know how many times you want to repeat the code.</p>
                
                <pre><code>// Syntax:
for (initialization; condition; increment) {
    // code to repeat
}</code></pre>
                
                <h4>Try it Yourself:</h4>
                <p>Modify the code to check if other numbers are prime.</p>
            `;
            lessonCode = `public class Main {
    public static void main(String[] args) {
        int n = 17; // Example number to check
        boolean isPrime = true;

        if (n <= 1) {
            isPrime = false;
        } else {
            for (int i = 2; i <= Math.sqrt(n); i++) {
                if (n % i == 0) {
                    isPrime = false;
                    break;
                }
            }
        }

        if (isPrime) {
            System.out.println(n + " is a prime number.");
        } else {
            System.out.println(n + " is not a prime number.");
        }
    }
}`;
            break;
        default:
            lessonContent = `
                <h3>Concept Explanation</h3>
                <p>This lesson covers advanced Java concepts. Continue building your knowledge with more complex examples.</p>
                
                <h4>Try it Yourself:</h4>
                <p>Experiment with the code in the editor and see how different approaches work.</p>
            `;
            lessonCode = `public class Main {
    public static void main(String[] args) {
        System.out.println("Welcome to Lesson ${lessonNumber}!");
        System.out.println("Continue practicing Java programming concepts.");
    }
}`;
    }
    
    // Update theory section
    document.querySelector('.theory-section').innerHTML = lessonContent;
    
    // Update editor with new code
    editor.setValue(lessonCode, -1);
    
    // Update quiz based on lesson content
    updateQuizForLesson(lessonNumber);
}

// Function to update quiz based on lesson
function updateQuizForLesson(lessonNumber) {
    const quizContainer = document.querySelector('.assessment-section');
    
    let quizHTML = '<h3>Knowledge Check</h3><form id="quiz-form">';
    
    switch(lessonNumber) {
        case 1:
            quizHTML += `
                <div class="question">
                    <p>1. Which of the following is the correct way to declare an integer variable in Java?</p>
                    <label><input type="radio" name="q1" value="A"> A) var number = 5;</label>
                    <label><input type="radio" name="q1" value="B"> B) int number = 5;</label>
                    <label><input type="radio" name="q1" value="C"> C) integer number = 5;</label>
                    <label><input type="radio" name="q1" value="D"> D) number int = 5;</label>
                </div>
                
                <div class="question">
                    <p>2. What is the purpose of the 'double' data type in Java?</p>
                    <label><input type="radio" name="q2" value="A"> A) To store whole numbers</label>
                    <label><input type="radio" name="q2" value="B"> B) To store decimal numbers</label>
                    <label><input type="radio" name="q2" value="C"> C) To store text</label>
                    <label><input type="radio" name="q2" value="D"> D) To store boolean values</label>
                </div>
            `;
            break;
        case 2:
            quizHTML += `
                <div class="question">
                    <p>1. What is the result of the expression: 10 > 5 ?</p>
                    <label><input type="radio" name="q1" value="A"> A) true</label>
                    <label><input type="radio" name="q1" value="B"> B) false</label>
                    <label><input type="radio" name="q1" value="C"> C) 10</label>
                    <label><input type="radio" name="q1" value="D"> D) 5</label>
                </div>
                
                <div class="question">
                    <p>2. Which operator is used for equality comparison in Java?</p>
                    <label><input type="radio" name="q2" value="A"> A) =</label>
                    <label><input type="radio" name="q2" value="B"> B) ==</label>
                    <label><input type="radio" name="q2" value="C"> C) !=</label>
                    <label><input type="radio" name="q2" value="D"> D) ></label>
                </div>
            `;
            break;
        case 3:
            quizHTML += `
                <div class="question">
                    <p>1. What is the purpose of the 'break' statement in a loop?</p>
                    <label><input type="radio" name="q1" value="A"> A) To skip the current iteration</label>
                    <label><input type="radio" name="q1" value="B"> B) To exit the loop completely</label>
                    <label><input type="radio" name="q1" value="C"> C) To restart the loop</label>
                    <label><input type="radio" name="q1" value="D"> D) To pause the loop</label>
                </div>
                
                <div class="question">
                    <p>2. How many times will this loop execute: for(int i=0; i<5; i++)?</p>
                    <label><input type="radio" name="q2" value="A"> A) 4 times</label>
                    <label><input type="radio" name="q2" value="B"> B) 5 times</label>
                    <label><input type="radio" name="q2" value="C"> C) 6 times</label>
                    <label><input type="radio" name="q2" value="D"> D) Infinite times</label>
                </div>
            `;
            break;
        default:
            quizHTML += `
                <div class="question">
                    <p>1. What have you learned in this lesson?</p>
                    <label><input type="radio" name="q1" value="A"> A) Something new about Java</label>
                    <label><input type="radio" name="q1" value="B"> B) Advanced programming concepts</label>
                    <label><input type="radio" name="q1" value="C"> C) Both A and B</label>
                    <label><input type="radio" name="q1" value="D"> D) Nothing</label>
                </div>
                
                <div class="question">
                    <p>2. How confident do you feel about the material?</p>
                    <label><input type="radio" name="q2" value="A"> A) Not confident</label>
                    <label><input type="radio" name="q2" value="B"> B) Somewhat confident</label>
                    <label><input type="radio" name="q2" value="C"> C) Confident</label>
                    <label><input type="radio" name="q2" value="D"> D) Very confident</label>
                </div>
            `;
    }
    
    quizHTML += '<button type="submit" class="btn-submit">Check Answers</button></form>';
    quizContainer.innerHTML = quizHTML;
    
    // Reattach event listener to the new form
    document.getElementById('quiz-form').addEventListener('submit', checkQuizAnswers);
}

// Function to scroll to a specific section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        window.scrollTo({
            top: section.offsetTop - 70,
            behavior: 'smooth'
        });
    }
}

// Function to load a specific course
function loadCourse(courseLevel) {
    // Show the learning interface
    document.getElementById('learning-interface').style.display = 'block';
    
    // Scroll to the learning interface
    scrollToSection('learning-interface');
    
    // Update the course header to show which course is selected
    document.querySelector('.lesson-title').textContent = `${getCourseTitle(courseLevel)} - Lesson 1`;
    
    // Load the first lesson for the selected course
    loadLesson(1);
}

// Helper function to get course title
function getCourseTitle(courseLevel) {
    switch(courseLevel) {
        case 'beginner': return 'Java Fundamentals';
        case 'intermediate': return 'Object-Oriented Programming';
        case 'advanced': return 'Advanced Java Concepts';
        default: return 'Java Course';
    }
}

// Function to load a video
function loadVideo(videoId) {
    // In a real implementation, this would load the actual video
    // For this demo, we'll just update the player with a placeholder
    const player = document.querySelector('.video-player');
    const videoInfo = document.querySelector('.video-info');
    
    // Update the video player
    player.innerHTML = `<p>Loading video: ${videoId}...</p>`;
    
    // Update video info based on the video ID
    let title = '';
    let description = '';
    
    switch(videoId) {
        case 'variables':
            title = 'Variables in Java';
            description = 'Learn about variables, data types, and how to declare and initialize them in Java';
            break;
        case 'operators':
            title = 'Arithmetic Operators';
            description = 'Understand how to perform mathematical operations in Java';
            break;
        case 'conditionals':
            title = 'Conditional Statements';
            description = 'Learn how to make decisions in your Java programs';
            break;
        case 'loops':
            title = 'Looping Constructs';
            description = 'Master the different types of loops in Java';
            break;
        default:
            title = 'Java Tutorial';
            description = 'Learn Java programming concepts';
    }
    
    videoInfo.innerHTML = `
        <h3>${title}</h3>
        <p>${description}</p>
    `;
}

// Simulate loading progress when page loads
window.addEventListener('load', function() {
    // Update progress UI after a delay to simulate loading
    setTimeout(updateProgressUI, 1000);
});