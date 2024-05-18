// Function to handle the Tab key press in the textarea
function enableTabIndentation(textarea) {
    textarea.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;

            // Set textarea value to: text before caret + four spaces + text after caret
            this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);

            // Put caret at right position again
            this.selectionStart = this.selectionEnd = start + 4;
        }
    });
}

// Load and display PDF content
function loadPDF(url, question) {
    document.getElementById('selectedQuestion').value = question;
    
    const pdfjsLib = window['pdfjs-dist/build/pdf'];
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.5.207/pdf.worker.min.js';

    pdfjsLib.getDocument(url).promise.then(function(pdf) {
        pdf.getPage(1).then(function(page) {
            const scale = 1.5;
            const viewport = page.getViewport({ scale: scale });

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            page.render({
                canvasContext: context,
                viewport: viewport
            }).promise.then(function() {
                const challengeContent = document.getElementById('challengeContent');
                challengeContent.innerHTML = ''; // Clear any previous content
                challengeContent.appendChild(canvas);
            });
        });
    });

    // Fetch and display initial code template
    fetch('/get_initial_code', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ pdf_name: question })
    })
    .then(response => response.json())
    .then(data => {
        const codeEditor = document.getElementById('codeEditor');
        codeEditor.value = data.initial_code;
        enableTabIndentation(codeEditor);  // Enable Tab key for indentation
    })
    .catch(error => console.error('Error:', error));

    // Fetch and display the best score for the selected question
    fetch('/get_best_score', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ pdf_name: question })
    })
    .then(response => response.json())
    .then(data => {
        const bestScoreElement = document.getElementById('bestScore');
        bestScoreElement.innerHTML = `Best Score: ${data.best_score}`;
        bestScoreElement.style.display = 'block';
    })
    .catch(error => {
        document.getElementById('bestScore').style.display = 'none';
        console.error('Error:', error);
    });
}

// Function to submit the solution
function submitSolution() {
    const fileInput = document.getElementById('fileInput');
    const codeEditor = document.getElementById('codeEditor');
    const selectedQuestion = document.getElementById('selectedQuestion').value;
    const formData = new FormData();

    formData.append('selectedQuestion', selectedQuestion);

    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    } else {
        const blob = new Blob([codeEditor.value], { type: 'text/plain' });
        formData.append('file', blob, 'solution.py');
    }

    fetch('/submit_code', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const resultElement = document.getElementById('result');
        resultElement.innerHTML = `<h3>Result</h3>
                                   <p>Testing question: ${selectedQuestion}</p>`;
        // resultElement.innerHTML += `<p>Best Score: ${data.best_score}</p>`;
        data.results.forEach(result => {
            resultElement.innerHTML += `<div class="test-result">${result}</div>`;
        });
        resultElement.innerHTML += `<p class="final-score">Final Score: <strong>${data.score}</strong></p>`;
    })
    .catch(error => console.error('Error:', error));
}

// Enable Tab key for indentation on page load
document.addEventListener('DOMContentLoaded', function () {
    const codeEditor = document.getElementById('codeEditor');
    enableTabIndentation(codeEditor);
});
