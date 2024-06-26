$(document).ready(function () {  
    $('#userMessage').focus();
    $('#sendMessageBtn').click(function () {
        sendMessage();
    });

    // Add event listener for suggestion boxes
    $('.suggestion-box').click(function() {
        var suggestionText = $(this).text();
        $('#userMessage').val(suggestionText); // Set the suggestion text in the input field
        sendMessage(); // Call sendMessage function
        $('.suggestion-grid').hide(); // Hide the suggestion grid after sending message
    });
  
    $('#userMessage').keypress(function (e) {
        if (e.which === 13) { // Enter key pressed
            sendMessage();
        }
    });
  
    function sendMessage() {
        var userMessage = $('#userMessage').val().trim();
        if (userMessage.length === 0) return;

        $('#loadingSpinner').show();
  
        var userMessageHtml =
            `<div class="chat message">
                <img src="../static/user.png">
                <span>${userMessage}</span>
            </div>`;
  
        $('#messageBox').append(userMessageHtml);
        $('#userMessage').val('');

        // Scroll to bottom after appending the user's message
        scrollToBottom();
  
        // Send message to Flask server
        $.ajax({
            type: 'POST',
            url: '/chatbot',
            data: { message: userMessage },
            success: function (response) {
                var botResponseHtml =
                    `<div class="chat response">
                        <img src="../static/musicrecco_chatbotprofile.png">
                        <span class="response-text">${response.response}</span>
                    </div>`;
                $('#messageBox').append(botResponseHtml);
                // Scroll to bottom after appending messages
                $('#loadingSpinner').hide();
                scrollToBottom();
            },
            error: function () {
                console.error('Error sending message');
                $('#loadingSpinner').hide();
            }
        });
    }

    // Function to scroll the message box to the bottom
    function scrollToBottom() {
        var messageBox = document.getElementById('messageBox');
        messageBox.scrollTop = messageBox.scrollHeight;
    }
});
