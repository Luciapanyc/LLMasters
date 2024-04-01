$(document).ready(function () {  
    $('#userMessage').focus();
    $('#sendMessageBtn').click(function () {
        sendMessage();
    });
  
    $('#userMessage').keypress(function (e) {
        if (e.which === 13) { // Enter key pressed
            sendMessage();
        }
    });
  
    function sendMessage() {
        var userMessage = $('#userMessage').val().trim();
        if (userMessage.length === 0) return;
  
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
                scrollToBottom();
            },
            error: function () {
                console.error('Error sending message');
            }
        });
    }
    // Function to scroll the message box to the bottom
    function scrollToBottom() {
        var messageBox = document.getElementById('messageBox');
        messageBox.scrollTop = messageBox.scrollHeight;
    }
});

  